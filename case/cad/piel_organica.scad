// LA PIEL ORGANICA -- propuesta del 2026-09-05, SIN FIRMAR.
//
//   openscad -o build/piel/<parte>.stl -D 'PART="<parte>"' piel_organica.scad
//   partes: mejillas | banda | aluminio | acrilico | madera
//
// Vive AL LADO de sam17_case.scad y no lo toca: reutiliza su perfil y sus
// piezas por `use`, y pone encima la piel del concepto de Samuel (tres
// renders, 05-09). Lo que propone, en una linea: el case de hoy es dos anillos
// de aluminio fresado (el hueso) con seis pieles encima --techo de chapa,
// nariz, talon, dos mejillas de acrilico y la trasera--; esto cambia cinco de
// esas pieles por UNA, y deja el hueso y la trasera donde estan.
//
// Que es cada parte:
//   mejillas   las dos, con la celosia de celosia_ramas.scad (celosia.py)
//   banda      la piel que envuelve el canto: nariz, techo, chaflanes y
//              talon, con las ventanas de las tres filas y de la trasera
//   aluminio   lo que sigue igual: rieles, paneles, marcos de ventana, los
//              dos anillos (ahora escondidos, y por eso ya no fresados con
//              cara vista) y la tapa del valle
//   acrilico   la trasera, que se queda tal cual (KONDOR, ondas, ranuras)
//   madera     la tabla y las paticas
//
// Lo que NO esta y en el case firmado si: nariz(), talon(), miembro_alto()
// (el techo) y costados() (las mejillas de acrilico) -- la piel los sustituye.
// Y chasis(): con la fuente afuera (v5) no hay chasis que meter.
//
// Las mejillas y la banda salen en DOS STL y no en uno a proposito: la
// mejilla lleva cientos de agujeros y OpenSCAD 2021 hace las uniones 3D con
// CGAL; unir esa malla con la banda tarda minutos y no compra nada, Blender
// las carga por separado con el mismo material.
include <params.scad>
include <celosia_ramas.scad>
use <sam17_case.scad>

PART = "mejillas";

piel_e      = 6;        // mm, espesor de la piel. Nylon MJF: 4-8 es lo normal
piel_solape = t_placa;  // el labio de la piel pisa el panel hasta la placa de
                        // anclaje y no mas: mas alla estorba al modulo al salir
                        // (las dos filas son tapa: nada fijo junto a un riel
                        // puede tapar su barrido)

// --- 2D sobre el perfil ------------------------------------------------
module perfil_ext() offset(r = piel_e) perfil_lateral();

// la piel no baja del suelo: ahi esta la tabla. El corte va piel_aire por
// encima de y = 0 y no en 0: cortar JUSTO en el canto de abajo del perfil deja
// el contorno interior tocando la linea de corte en todo un segmento, y esa
// figura extruye a una malla que CGAL no da por cerrada (OpenSCAD 2021.01,
// medido: con el corte en 0 la banda no exporta; en 0.3 si).
piel_aire = 0.3;
module sobre_suelo_2d() intersection() { children(); translate([-100, piel_aire]) square([700, 500]); }

// LA CELOSIA SON RAMAS, no celdas (desde el segundo render del 05-09: Samuel
// pidio "esa forma organica que parece modernista y parecen ramas de arbol").
// celosia.py las hace crecer desde el marco y las escribe como segmentos
// [x0, y0, x1, y1, w]; aqui cada uno es una capsula de grosor w, y el cierre
// morfologico (dilatar r, erosionar r) suelda las horquillas y redondea las
// uniones, que es lo que hace que lean a rama y no a alambre. Lo abierto es
// el hueco del marco MENOS las ramas.
module rama_2d(s) {
    $fn = 24;
    hull() {
        translate([s[0], s[1]]) circle(d = s[4]);
        translate([s[2], s[3]]) circle(d = s[4]);
    }
}

module ramas_2d()
    offset(r = -celosia_cierre) offset(r = celosia_cierre)
        union() for (s = celosia_ramas) rama_2d(s);

module celosia_2d()
    difference() {
        offset(delta = -celosia_borde) perfil_lateral();
        ramas_2d();
    }

module mejilla_2d() sobre_suelo_2d() difference() { perfil_ext(); celosia_2d(); }

module mejilla(z0) translate([0, 0, z0]) linear_extrude(piel_e) mejilla_2d();

module mejillas() { mejilla(-piel_e); mejilla(ancho_total); }

// --- la banda del canto -------------------------------------------------
module banda_2d() sobre_suelo_2d() difference() { perfil_ext(); perfil_lateral(); }

// normal hacia FUERA de la arista A->B del perfil, que va en sentido horario
function nrm(A, B) = let (d = B - A, L = norm(d)) [-d.y, d.x] / L;

module cara_quad(A, B, dentro = 1, fuera = 3*piel_e) {
    n = nrm(A, B);
    polygon([A - n*dentro, B - n*dentro, B + n*fuera, A + n*fuera]);
}

// las tres caras de las filas, P1->P2->P3->P4: la banda se abre entera entre
// los labios de los extremos. Entre filas no hay piel, como hoy no hay chapa:
// ahi estan la tapa del valle y los rieles.
module ventana_filas_2d() {
    P = pts_perfil();
    for (i = [1 : 3]) cara_quad(P[i], P[i + 1]);
    translate(P[2]) circle(r = 3*piel_e);
    translate(P[3]) circle(r = 3*piel_e);
}

// la trasera: el campo visible de hoy (entre el labio del talon y el del
// techo), y la piel hace de marco arriba y abajo como hoy lo hacen las chapas
module ventana_trasera_2d() {
    P = pts_perfil();
    c = trasera_campo();
    translate([P[6].x - 1, c[0]]) square([3*piel_e + 1, c[1] - c[0]]);
}

module banda()
    difference() {
        translate([0, 0, -piel_e]) linear_extrude(ancho_total + 2*piel_e) banda_2d();
        translate([0, 0, t_anillo + piel_solape])
            linear_extrude(ancho_total - 2*(t_anillo + piel_solape)) ventana_filas_2d();
        translate([0, 0, t_anillo])
            linear_extrude(ancho_total - 2*t_anillo) ventana_trasera_2d();
    }

// --- lo que sigue igual ---------------------------------------------------
// Los paneles van en STL propio: en el concepto son aluminio OSCURO dentro de
// la piel blanca, y ese contraste es la idea (panel duro en marco blando).
// Pintarlos del aluminio claro de render.py los funde con la piel.
module aluminio() { rails(); marcos_ventana(); costillas(); tapa_valle(); }
module acrilico() { piel_trasera(); }
module madera()   { bandeja_base(); paticas(); }

if      (PART == "mejillas") mejillas();
else if (PART == "banda")    banda();
else if (PART == "aluminio") aluminio();
else if (PART == "paneles")  paneles();
else if (PART == "acrilico") acrilico();
else if (PART == "madera")   madera();
else if (PART == "todo")     { mejillas(); banda(); aluminio(); paneles(); acrilico(); madera(); }
else assert(false, str("PART desconocida: ", PART));

echo(str("PIEL: espesor ", piel_e, ", celosia de ", celosia_n, " ramas, borde ",
         celosia_borde, ", abierto ", celosia_abierto_mm2, " mm2 por mejilla (",
         100*celosia_abierto, " % del perfil), respira ", celosia_abierto_ventana_mm2));
