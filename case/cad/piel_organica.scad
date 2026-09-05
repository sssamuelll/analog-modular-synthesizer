// LA PIEL ORGANICA -- propuesta del 2026-09-05, SIN FIRMAR.
//
//   openscad -o build/piel/<parte>.stl -D 'PART="<parte>"' piel_organica.scad
//   partes: banda | aluminio | paneles | acrilico | madera
//
// Vive AL LADO de sam17_case.scad y no lo toca: reutiliza su perfil y sus
// piezas por `use`, y pone encima la piel del concepto de Samuel (cinco
// imagenes, 05-09). Lo que propone, en una linea: el case de hoy es dos
// anillos de aluminio fresado (el hueso) con seis pieles encima --techo de
// chapa, nariz, talon, dos mejillas de acrilico y la trasera--; esto cambia
// cinco de esas pieles por UNA, y deja el hueso y la trasera donde estan.
//
// LA PIEL ES UN ARBOL (Samuel, 05-09): la cubierta es el TRONCO y cada
// cachete una RAMA. Ninguna de las dos es plana, y por eso desde la cuarta
// version YA NO SALEN DE AQUI: las levanta case/renders/imprimir_piel.py en
// Blender --el cachete de case/cad/celosia_rama.json (celosia.py), tubos de
// seccion redonda con marco de almohada; la cubierta a partir de la banda de
// abajo, con la corteza puesta por desplazamiento--. Lo que queda en este
// archivo es la LAMINA base de la cubierta y lo que sigue igual.
//
// Que es cada parte:
//   banda      la lamina de 6 mm que envuelve el canto: nariz, techo,
//              chaflanes y talon, con las ventanas de las tres filas y de la
//              trasera. DE UNA PIEZA: un tronco no viene partido por la mitad
//              (Samuel, 05-09: "no estoy convencido de partir la banda"); que
//              no quepa en una MJF de serie es la decision D-P6 del papel
//   aluminio   lo que sigue igual: rieles, marcos de ventana, los dos anillos
//              (ahora escondidos, y por eso ya no fresados con cara vista) y
//              la tapa del valle
//   paneles    los tres, en STL propio (van oscuros en el render)
//   acrilico   la trasera, que se queda tal cual (KONDOR, ondas, ranuras)
//   madera     la tabla y las paticas
//
// Lo que NO esta y en el case firmado si: nariz(), talon(), miembro_alto()
// (el techo) y costados() (las mejillas de acrilico) -- la piel los sustituye.
// Y chasis(): con la fuente afuera (v5) no hay chasis que meter.
include <params.scad>
use <sam17_case.scad>

PART = "banda";

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

if      (PART == "banda")    banda();
else if (PART == "aluminio") aluminio();
else if (PART == "paneles")  paneles();
else if (PART == "acrilico") acrilico();
else if (PART == "madera")   madera();
else if (PART == "todo")     { banda(); aluminio(); paneles(); acrilico(); madera(); }
else assert(false, str("PART desconocida: ", PART));

echo(str("PIEL: lamina de la cubierta de ", piel_e, " mm, de una pieza; el cachete y la corteza salen de imprimir_piel.py"));
