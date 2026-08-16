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
// remate superior trasero. Centros [x, y]:
function centros_esqueleto() =
    let (P = pts_perfil(), r = rail/2)
    [[r + 2,               r],                       // base delantera
     [prof_inferior - r,   r],                       // base trasera
     [P[3].x + r,          P[3].y - r],               // entrepiso delantero
     [prof_inferior - r,   P[6].y - r],               // entrepiso trasero
     [prof_superior - r,   P[5].y - r]];              // remate superior

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

module bandeja_base_2d() {
    au = ancho_total - 2*t_cheek;
    difference() {
        plancha(au, prof_inferior - 2*rail - 4);
        fila_agujeros(au, rail/2);
        fila_agujeros(au, prof_inferior - 2*rail - 4 - rail/2);
        // ventilacion bajo el PSU (tercio derecho): onda cuadrada
        translate([au*0.68, (prof_inferior-2*rail-4)*0.35])
            onda("cuadrada", au*0.25);
    }
}

module bandeja_entrepiso_2d() {
    au = ancho_total - 2*t_cheek;
    P = pts_perfil();
    fondo = prof_inferior - P[3].x - 2*rail;
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

module zocalo_2d() {
    au = ancho_total - 2*t_cheek;
    difference() {
        plancha(au, alto_frontal - alto_pie);
        fila_agujeros(au, rail/2);
    }
}

// --- pieles traseras flotantes (standoffs M4, junta de sombra) --------
module piel_inferior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    P = pts_perfil();
    alto = P[6].y - 2*gap_sombra;
    difference() {
        plancha(au, alto);
        for (c = [[15,15],[au-15,15],[15,alto-15],[au-15,alto-15]])
            translate(c) circle(d = d_M4_paso + kerf);
        translate([au*0.10, alto*0.62]) onda("triangulo", au*0.35);
        translate([au*0.55, alto*0.62]) onda("cuadrada",  au*0.35);
        // recorte IEC C14 con interruptor (bloque snap-in tipico
        // 48 x 27.5; CONFIRMAR contra el datasheet de la pieza comprada)
        translate([au - 70, 22]) square([48, 27.5]);
    }
}

module piel_superior_2d() {
    au = ancho_total - 2*t_cheek - 2*gap_sombra;
    P = pts_perfil();
    alto = P[4].y - P[6].y - 2*gap_sombra;
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
// Dos costados en los extremos de Z; 9 largueros 2020 (centros_rail() +
// centros_esqueleto(), en ese orden) cruzando entre sus caras internas.
module costados() {
    costado();
    translate([0, 0, ancho_total - t_cheek]) costado();
}

module rails() {
    for (c = concat(centros_rail(), centros_esqueleto()))
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
// paredes verticales (grosor crece hacia dentro en X).
module bandeja_base() {
    translate([rail, rail + t_acrilico, ancho_total - t_cheek])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_acrilico) bandeja_base_2d();
}

module bandeja_entrepiso() {
    P = pts_perfil();
    translate([P[3].x + rail, P[3].y + t_acrilico, ancho_total - t_cheek])
        rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(t_acrilico) bandeja_entrepiso_2d();
}

module zocalo() {
    translate([0, alto_pie, ancho_total - t_cheek])
        rotate([0, 90, 0])
            linear_extrude(t_acrilico) zocalo_2d();
}

module piel_inferior() {
    P = pts_perfil();
    translate([P[8].x - gap_sombra, gap_sombra, t_cheek + gap_sombra])
        rotate([0, -90, 0])
            linear_extrude(t_acrilico) piel_inferior_2d();
}

module piel_superior() {
    P = pts_perfil();
    translate([P[6].x - gap_sombra, P[6].y + gap_sombra, t_cheek + gap_sombra])
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
    x4 = x3 + au + sep;  translate([x4, y2]) piel_inferior_2d();
    x5 = x4 + aup + sep; translate([x5, y2]) piel_superior_2d();
    %square([1000, 600]);
}

module bom() {
    au = ancho_total - 2*t_cheek;
    echo(str("BOM: larguero 2020 x", len(centros_rail()) + len(centros_esqueleto()),
             " de ", au, " mm"));
    echo(str("BOM: tornillo M5 boton x", 2*(len(centros_rail()) + len(centros_esqueleto()))));
    echo("BOM: standoff M4 x8 (pieles) + tornillo M4 boton x16 + arandela x16");
    echo(str("BOM: planchas t=", t_acrilico, ": base, entrepiso, zocalo, ",
             "piel inf, piel sup; costados t=", t_cheek, " x2"));
}
