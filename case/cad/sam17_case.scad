// sam17_case.scad — consola de dos pisos en acrilico naranja (spec rev. 3).
// Fuente de verdad dimensional: params.scad. Este fichero DIBUJA;
// clearance_budget.py DECIDE. Angulos desde la vertical.
//
//   openscad -o out.stl -D 'PART="costado"'    sam17_case.scad
//   openscad -o out.dxf -D 'PART="costado_2d"' sam17_case.scad

include <params.scad>
PART = "assembly";
$fn = 48;

// ancho interior entre costados; Tasks 4-5 lo consumen como ancho_util.
ancho_util = ancho_total - 2*t_cheek;

// vertices del perfil lateral (X = fondo, Y = arriba) — misma numeracion
// que clearance_budget.perfil(): p0..p8
function pts_perfil() =
    let (si = sin(angulo_inferior), ci = cos(angulo_inferior),
         ss = sin(angulo_superior), cs = cos(angulo_superior),
         ye = alto_frontal + alto_panel*ci,          // y entrepiso
         x2 = alto_panel*si,                          // fin cara inferior
         x3 = x2 + paso_horizontal,
         x4 = x3 + alto_panel*ss,
         yt = ye + alto_panel*cs)                     // alto total
    [[0,0],[0,alto_frontal],[x2,ye],[x3,ye],[x4,yt],
     [prof_superior,yt],[prof_superior,ye],[prof_inferior,ye],
     [prof_inferior,0]];

// puntos medios de rail por cara: [origen, direccion] de cada cara y
// centros a inset_tornillo y alto_panel-inset_tornillo sobre la cara,
// retirados hacia dentro t_panel + rail/2 segun la normal
function centros_rail() =
    let (P = pts_perfil(),
         caras = [[P[1], P[2]], [P[3], P[4]]],
         off = t_panel + rail/2)
    [for (c = caras, s = [inset_tornillo, alto_panel - inset_tornillo])
        let (d = (c[1]-c[0])/norm(c[1]-c[0]),      // unitario de la cara
             n = [d.y, -d.x])                       // normal hacia dentro
        c[0] + d*s + n*off];

// largueros del esqueleto (2020) que no son railes de panel:
// base delantera, base trasera, entrepiso delantero, entrepiso trasero,
// remate superior, repisa, zocalo superior. Centros [x, y]:
//
// entrepiso delantero reubicado (fix de solape, ronda de revision 1): el
// original P[3].x+r invadia el rail de panel cara-superior s=inset_tornillo
// (17.6x12.6 mm de solape, verificado). Ahora se apoya holgura_rail detras
// del borde trasero de ESE rail. Y de ambos railes de entrepiso baja a
// P3.y-t_acrilico-r para que la bandeja apoye con el CANTO SUPERIOR a ras
// de P3.y (antes apoyaba con el canto inferior ahi, dejando la tapa 5 mm
// por encima del plano de entrepiso).
//
// repisa (sexto larguero, ronda de revision 2 — R6): ancla piel_superior
// SIN pasar por el rail entrepiso-trasero (ese vive en X=340, en el plano
// del piso inferior; piel_superior vuela en X=prof_superior+gap_sombra=255,
// el plano del piso superior — anclarla ahi invadia la bandeja de
// entrepiso). Centro a P3.y+15: canto inferior del rail en P3.y+5 (5 mm
// por encima del tope de la bandeja, sin tocarla) y la fila de agujero
// inferior de piel_superior (inset 15) cae justo en P3.y, a ras del tope
// de la bandeja.
//
// zocalo superior (septimo larguero, ronda final): la fila SUPERIOR del
// zocalo anclaba al rail de panel cara-inferior s=inset, que R3 gira 12
// grados — tornillo entrando en diagonal y arandela de canto sobre
// acrilico. PRINCIPIO: las placas anclan unicamente a railes de ESQUELETO,
// sin rotar; los railes de panel estan rotados porque sirven a los paneles.
// No cabia un larguero a la altura del de panel (el hueco entre el tope de
// bandeja_base y la esquina baja del rail girado mide 15.6 mm, menos que
// los 20 del perfil), asi que este se retira en X: se planta holgura_rail
// detras de la esquina mas saliente del rail girado (semiextension
// r*(cos+sin) del cuadrado rotado) y su centro cae a alto_frontal-15, de
// modo que el canto SUPERIOR del zocalo termina exacto en alto_frontal
// (antes sobrepasaba 17.5 mm y tapaba la fila de tornillos del panel).
// Canto inferior del rail a ras del tope de bandeja_base: contacto por
// diseno, cero solape.
function centros_esqueleto() =
    let (P = pts_perfil(), r = rail/2, cr = centros_rail(),
         x_ed = cr[2].x + rail + holgura_rail,
         y_ep = P[3].y - t_acrilico - r,
         he_ci = r * (cos(angulo_inferior) + sin(angulo_inferior)),
         x_zs = cr[0].x + he_ci + holgura_rail + r)
    [[r + 2,               r],                       // base delantera
     [prof_inferior - r,   r],                       // base trasera
     [x_ed,                y_ep],                     // entrepiso delantero
     [prof_inferior - r,   y_ep],                     // entrepiso trasero
     [prof_superior - r,   P[5].y - r],               // remate superior
     [prof_superior - r,   P[3].y + 15],              // repisa (R6)
     [x_zs,                alto_frontal - 15]];       // zocalo superior

module perfil_lateral() { polygon(pts_perfil()); }

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
    fondo = prof_inferior - ce[2].x + rail/2;   // canto delantero a ras del rail reubicado
    difference() {
        plancha(au, fondo);
        fila_agujeros(au, rail/2);
        fila_agujeros(au, fondo - rail/2);
        // pasacables entre pisos: 3 oblongos de 40 x 12
        for (x = [au*0.2, au*0.5, au*0.8])
            translate([x, fondo/2]) hull()
                for (dx = [-14, 14]) translate([dx, 0]) circle(d = 12 + kerf);
    }
}

// zocalo volado sobre standoffs M4 (R1, ronda de revision): antes bolonado
// directo al rail base-delantera con una sola fila M3, y=10 quedaba a solo
// 3 mm de holgura del rail (invadido en Y por 12 mm). Ahora comparte el
// mismo esquema que las pieles: 4 esquinas M4, filas a ras de sus dos
// railes limite — los DOS del esqueleto (base delantera / zocalo superior)
// desde la ronda final: la fila de arriba anclaba al rail de PANEL
// cara-inferior s=inset, y ese va rotado 12 grados (ver centros_esqueleto()).
module zocalo_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;   // volado, mismo ancho que las pieles
    ce = centros_esqueleto();
    alto = ce[6].y - ce[0].y + 30;                  // filas (inset 15) a ras de ambos railes
    difference() {
        plancha(au, alto);
        for (c = [[15,15],[au-15,15],[15,alto-15],[au-15,alto-15]])
            translate(c) circle(d = d_M4_paso + kerf);
    }
}

// --- pieles traseras flotantes (standoffs M4, junta de sombra) --------
// alto: filas de agujero (inset 15 mm) a ras de las centrelineas de los
// dos railes limite de cada tramo (R1, ronda de revision — antes el alto
// salia de un inset de gap_sombra sobre el perfil y quedaba invadiendo el
// rail trasero correspondiente; ver centros_esqueleto()).
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
else if (PART == "zocalo_2d")            zocalo_2d();
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
    cr = centros_rail();                              // [cara_inf x2, cara_sup x2]
    angs = [angulo_inferior, angulo_inferior, angulo_superior, angulo_superior];
    for (i = [0 : 3])
        translate([cr[i].x, cr[i].y, ancho_total/2])
            rotate([0, 0, -angs[i]])
                rotate([90, 0, 0])
                    rail_2020(ancho_util);
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

// volado: cara interior (la que mira al cuerpo) a X=-gap_sombra, engrosa
// hacia -X. y0 deriva de la fila de agujero inferior (inset 15) cayendo
// en el rail base-delantera (ce[0].y), igual que en zocalo_2d().
module zocalo() {
    ce = centros_esqueleto();
    translate([-gap_sombra - t_acrilico, ce[0].y - 15, ancho_total - t_cheek - gap_sombra])
        rotate([0, 90, 0])
            linear_extrude(t_acrilico) zocalo_2d();
}

// volado: cara interior a X = prof_inferior + gap_sombra (fuera del
// cuerpo, no ya recortado hacia dentro), engrosa hacia +X. y0 deriva de
// la fila de agujero inferior cayendo en el rail base-trasera (ce[1].y).
module piel_inferior() {
    P = pts_perfil();
    ce = centros_esqueleto();
    translate([P[8].x + gap_sombra + t_acrilico, ce[1].y - 15, t_cheek + gap_sombra])
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
    zocalo();
    piel_inferior();
    piel_superior();
}

// panel de modulo (PCB de aluminio, t_panel) sobre una cara del perfil
// A->B: cara externa a ras del perfil, engrosa hacia dentro segun la
// misma normal que centros_rail() ([d.y,-d.x]).
module panel_cara(A, B) {
    d = (B - A) / norm(B - A);
    translate([A.x, A.y, t_cheek])
        rotate([0, 0, atan2(d.y, d.x)])
            translate([0, -t_panel, 0])
                cube([norm(B - A), t_panel, ancho_util]);
}

module paneles() {
    P = pts_perfil();
    panel_cara(P[1], P[2]);   // cara inferior (procesamiento, 12 grados)
    panel_cara(P[3], P[4]);   // cara superior (generacion, 35 grados)
}

module assembly() {
    costados();
    rails();
    planchas_acrilico();
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
    // fila 2: las 5 planchas del cuerpo
    y2 = alto + sep;
    x1 = 0;              translate([x1, y2]) bandeja_base_2d();
    x2 = x1 + au + sep;  translate([x2, y2]) bandeja_entrepiso_2d();
    x3 = x2 + au + sep;  translate([x3, y2]) zocalo_2d();
    x4 = x3 + aup + sep; translate([x4, y2]) piel_inferior_2d();   // zocalo ahora ancho aup (volado, R1)
    x5 = x4 + aup + sep; translate([x5, y2]) piel_superior_2d();
    %square([1000, 600]);
}

module bom() {
    au = ancho_total - 2*t_cheek;
    echo(str("BOM: larguero 2020 x", len(centros_rail()) + len(centros_esqueleto()),
             " de ", au, " mm"));
    echo(str("BOM: tornillo M5 boton x", 2*(len(centros_rail()) + len(centros_esqueleto()))));
    echo("BOM: standoff M4 x12 (pieles+zocalo, volados) + tornillo M4 boton x24 + arandela x24");
    echo(str("BOM: planchas t=", t_acrilico, ": base, entrepiso, zocalo, ",
             "piel inf, piel sup; costados t=", t_cheek, " x2"));
}
