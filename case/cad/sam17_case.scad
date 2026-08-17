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

// puntos medios de rail por cara: [origen, fin, alto, inset de arranque,
// inset de remate] y centros sobre la cara a esos dos insets, retirados hacia
// dentro t_panel + rail/2 segun la normal.
//
// Los DOS insets de cada cara son distintos (ver la tabla de insets en
// params.scad): la punta redondeada del frente vacia 15 mm de cara y el pico
// del valle solo 2.6, asi que exigir el mismo inset en los dos extremos
// regalaria 12 mm de altura de piso sin comprar nada.
//
// SON TRES, NO CUATRO. La punta de arriba de la cara superior no lleva 2020:
// lleva la BISAGRA (ver eje_visagra()). Por eso el costado tampoco lleva
// taladro ahi -- costado_2d() perfora esta lista, y la bisagra no cuelga del
// acrilico sino del larguero de remate.
function centros_rail() =
    let (P = pts_perfil(),
         off = t_panel + rail/2,
         // [origen, fin, los s sobre la cara que llevan 2020]
         caras = [[P[1], P[2], [inset_inf_frente,
                                alto_cara_inf - inset_inf_valle]],
                  [P[3], P[4], [inset_sup_valle]]])
    [for (c = caras, s = c[2])
        let (d = (c[1]-c[0])/norm(c[1]-c[0]),      // unitario de la cara
             n = [d.y, -d.x])                       // normal hacia dentro
        c[0] + d*s + n*off];

// Eje de giro de la tapa superior. Va sobre la cara, a inset_sup_remate de su
// punta -- o sea EXACTAMENTE en la fila de taladros de arriba del panel, que
// EUROrack pone a 3.0 mm del canto --, y retirado hacia dentro lo justo para
// que el nudillo quede pegado al dorso del panel (t_panel + d_visagra/2).
// El panel remata por tanto a ras del vertice, que es lo que Samuel pidio para
// que la tapa pueda levantarse sin acrilico por encima estorbando.
function eje_visagra() =
    let (P = pts_perfil(),
         d = (P[4]-P[3])/norm(P[4]-P[3]),
         n = [d.y, -d.x])
    P[3] + d*(alto_cara_sup - inset_sup_remate) + n*(t_panel + d_visagra/2);

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
         // semiextension en X de un rail de panel TRAS su rotacion: el
         // cuadrado girado sobresale r*(cos+sin) de su centro, no r. Los dos
         // largueros que se plantan detras de un rail girado usan esta cota.
         he_cs = r * (cos(angulo_superior) + sin(angulo_superior)),
         x_ed = cr[2].x + he_cs + holgura_rail + r,
         y_ep = P[3].y - t_acrilico - r,
         // Remate superior. Su Y NO puede ser P[5].y - r: al acortar el marco
         // de arriba para que la esquina se lea como PUNTA, el rincon se
         // cierra y ahi ya no cabe. Tres techos, y manda el mas bajo:
         //   1. el TECHO YA REDONDEADO. La esquina trasera de arriba lleva
         //      tangente marco_remate/2, y como este larguero vive pegado al
         //      plano trasero (x = fondo - r), su esquina de atras cae justo
         //      donde el arco ya bajo esa tangente. P[5].y - r a secas lo
         //      dejaba FUERA del acrilico.
         //   2. el plano del panel de arriba: centro a r + t_panel de
         //      distancia PERPENDICULAR, con la normal interior (cos, -sen)
         //   3. la BISAGRA, que es la que de verdad manda. Antes este techo
         //      lo ponia el rail de panel del remate; ese rail ya no existe
         //      (lo sustituyo el eje de giro) y su sitio lo ocupa el nudillo,
         //      del que el remate tiene que quedar holgura_rail por debajo.
         y_rs = min(P[5].y - r - marco_remate/2,
                    P[3].y + (cos(angulo_superior)*(fondo() - r - P[3].x)
                              - (r + t_panel)) / sin(angulo_superior),
                    eje_visagra().y - d_visagra/2 - holgura_rail - r))
    // Los dos largueros de la base viven en las esquinas de abajo, que son
    // justo las que el redondeo VACIA. No basta plantarlos a ras: hay que
    // retirarlos hasta donde acaba la curva.
    //   - Frente: el radio en punta se recorta a la mitad de la arista mas
    //     corta, que es la cara frontal, asi que las dos tangentes se juntan
    //     en su punto medio y la curva muere a alto_frontal/2 del vertice.
    //   - Fondo: esquina de 90 grados con radio_perfil, tangente = radio_perfil.
    // Sin esto, check_dxf los acusaba de salirse del acrilico (esquinas en
    // (2.0, 0.0) y (405.0, 0.0), las dos dentro del trozo que quita la curva).
    [[alto_frontal/2 + r + 2,          r],           // base delantera
     [fondo() - r - radio_perfil, r],          // base trasera
     [x_ed,                y_ep],                     // entrepiso delantero
     [fondo() - r,   y_ep],                     // entrepiso trasero
     [fondo() - r,   y_rs],                     // remate superior
     [fondo() - r,   P[3].y + 15]];             // repisa (R6)

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
    difference() {
        perfil_lateral();
        for (c = concat(centros_rail(), centros_esqueleto()))
            translate(c) circle(d = d_M5_paso + kerf);
    }
}

module costado() { linear_extrude(t_cheek) costado_2d(); }

module rail_2020(largo) { cube([rail, largo, rail], center = true); }

// --- planchas rectangulares del cuerpo (todas t_acrilico) -------------
// Agujeros M3 de tuerca T cada ~100 mm contra los largueros 2020.
module fila_agujeros(largo, y, paso = 100, d = d_M3_paso)
    for (x = [paso/2 : paso : largo - paso/4])
        translate([x, y]) circle(d = d + kerf);

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
    x0 = ce[0].x - rail/2;                  // canto delantero a ras del rail
    fondo = ce[1].x + rail/2 - x0;          // canto trasero a ras del rail
    difference() {
        plancha(au, fondo);
        fila_agujeros(au, rail/2);          // -> x0 + rail/2 = ce[0].x
        fila_agujeros(au, fondo - rail/2);  // -> x0 + fondo - rail/2 = ce[1].x
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

module piel_inferior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    ce = centros_esqueleto();
    alto = ce[3].y - ce[1].y + 30;   // entrepiso trasero <-> base trasera
    difference() {
        plancha(au, alto);
        for (c = [[15,15],[au-15,15],[15,alto-15],[au-15,alto-15]])
            translate(c) circle(d = d_M4_paso + kerf);
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
        for (c = [[15,15],[au-15,15],[15,alto-15],[au-15,alto-15]])
            translate(c) circle(d = d_M4_paso + kerf);
        translate([au*0.15, alto*0.45]) onda("sierra", au*0.70);
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
    cr = centros_rail();                    // [inf frente, inf valle, sup valle]
    angs = [angulo_inferior, angulo_inferior, angulo_superior];
    for (i = [0 : len(cr) - 1])
        translate([cr[i].x, cr[i].y, ancho_total/2])
            rotate([0, 0, -angs[i]])
                rotate([90, 0, 0])
                    rail_2020(ancho_util);
    for (c = centros_esqueleto())
        translate([c.x, c.y, ancho_total/2])
            rotate([90, 0, 0])
                rail_2020(ancho_util);
    visagra();
}

// Bisagra continua de la tapa superior: el nudillo corre por el vertice del
// techo, de costado a costado. Aqui va solo el nudillo -- las palas (una al
// dorso del panel, otra al larguero de remate) son herraje, no geometria de
// corte, y se cierran al comprar la pieza.
module visagra() {
    e = eje_visagra();
    // el cilindro nace en +Z, que aqui ya es el ancho del case: sin girar.
    translate([e.x, e.y, t_cheek]) cylinder(h = ancho_util, d = d_visagra);
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
    ce = centros_esqueleto();
    translate([ce[0].x - rail/2, rail + t_acrilico, ancho_total - t_cheek])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_acrilico) bandeja_base_2d();
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

module planchas_acrilico() {
    bandeja_base();
    bandeja_entrepiso();
    piel_inferior();
    piel_superior();
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

// Paticas torneadas bajo los costados. En X caen sobre los dos rieles de
// base, que es donde esta la estructura; en Z su cara exterior queda a ras
// del canto del case (centro a d_pie/2) para que la carga del costado baje
// recta al pie y no de canto.
module paticas() {
    ce = centros_esqueleto();
    for (x = [ce[0].x, ce[1].x])
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
    %square([1000, 600]);
}

module bom() {
    au = ancho_total - 2*t_cheek;
    echo(str("BOM: larguero 2020 x", len(centros_rail()) + len(centros_esqueleto()),
             " de ", au, " mm"));
    echo(str("BOM: tornillo M5 boton x", 2*(len(centros_rail()) + len(centros_esqueleto()))));
    echo("BOM: standoff M4 x8 (las dos pieles, voladas) + tornillo M4 boton x16 + arandela x16");
    echo(str("BOM: bisagra continua x1 de ", au, " mm, nudillo d=", d_visagra,
             " (tapa superior; palas al dorso del panel y al larguero de remate)"));
    echo(str("BOM: patica metalica torneada x4, d=", d_pie, " x ", alto_pie, " mm"));
    echo(str("BOM: planchas t=", t_acrilico, ": base, entrepiso, ",
             "piel inf, piel sup; costados t=", t_cheek, " x2"));
}
