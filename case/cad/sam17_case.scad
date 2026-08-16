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
                for (dx = [-14, 14]) translate([dx, 0]) circle(d = 12);
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
            translate(pts[i])   circle(d = vent_ancho_ranura);
            translate(pts[i+1]) circle(d = vent_ancho_ranura);
        }
}

if (PART == "costado")             costado();
else if (PART == "costado_2d")     costado_2d();
else if (PART == "assembly")       assembly();
else if (PART == "bandeja_base_2d")      bandeja_base_2d();
else if (PART == "bandeja_entrepiso_2d") bandeja_entrepiso_2d();
else if (PART == "zocalo_2d")            zocalo_2d();
else if (PART == "piel_inferior_2d")     piel_inferior_2d();
else if (PART == "piel_superior_2d")     piel_superior_2d();
else assert(false, str("PART desconocido: ", PART));

// costado_2d vive en el plano XY del perfil (X = fondo, Y = altura);
// costado() lo extruye en +Z por t_cheek, o sea Z pasa a ser el ancho.
// Dos costados en los extremos de Z; 9 largueros 2020 (centros_rail() +
// centros_esqueleto(), en ese orden) cruzando entre sus caras internas.
module assembly() {                    // crece en Tasks 4-5
    costado();
    translate([0, 0, ancho_total - t_cheek]) costado();
    for (c = concat(centros_rail(), centros_esqueleto()))
        translate([c.x, c.y, ancho_total/2])
            rotate([90, 0, 0])
                rail_2020(ancho_util);
}
