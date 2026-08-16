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

if (PART == "costado")         costado();
else if (PART == "costado_2d") costado_2d();
else if (PART == "assembly")   assembly();
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
