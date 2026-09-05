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
//   mejillas   las dos, con la celosia de celosia_nervios.scad (celosia.py)
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
include <celosia_nervios.scad>
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

// LA CELOSIA SON FIBRAS de un campo de flujo (tercera version del 05-09; la
// referencia es el despiece de Samuel: nervios que se abanican desde el
// rincon de abajo-delante, se parten y se juntan dejando lentes escalonadas).
// celosia.py las integra y las escribe como segmentos [x0, y0, x1, y1, w];
// aqui cada uno es una capsula de grosor w, y el cierre morfologico (dilatar
// r, erosionar r) suelda las uniones y las redondea, que es lo que hace que
// lean a nervio y no a alambre. Lo abierto es el hueco del marco MENOS los
// nervios.
module rama_2d(s) {
    $fn = 24;
    hull() {
        translate([s[0], s[1]]) circle(d = s[4]);
        translate([s[2], s[3]]) circle(d = s[4]);
    }
}

module ramas_2d()
    offset(r = -celosia_cierre) offset(r = celosia_cierre)
        union() for (s = celosia_nervios) rama_2d(s);

module celosia_2d()
    difference() {
        offset(delta = -celosia_marco) perfil_lateral();
        ramas_2d();
    }

// AGUJEROS DE MONTAJE (el despiece de Samuel los ensena en las esquinas): el
// cachete se atornilla al anillo desde fuera. Van a `montaje_a` del perfil,
// dentro de la cara vista del anillo (cara_anillo = 20) y dentro del marco
// macizo (celosia_marco = 17), uno por tramo largo y dos en los largos. El
// anillo necesita las roscas M4 correspondientes en su cara exterior: eso es
// una enmienda a sam17_case.scad cuando esto se firme, no de este archivo.
// Pasantes lisos, sin avellanar: avellanar es una diferencia 3D sobre una
// malla de 1500 agujeros (CGAL, minutos) y una cabeza vista es lo que el
// despiece ensena.
montaje_d = 4.5;    // mm, pasante para M4
montaje_a = 9.0;    // mm, del canto del perfil al eje del tornillo
function _pt_tramo(A, B, f) = A + (B - A) * f;
module agujeros_montaje_2d() {
    P = pts_perfil();
    // [tramo A, tramo B, fracciones a lo largo]: abajo x2, frente-bajo x1,
    // frente-alto x1, techo x1, trasera x2
    tramos = [[P[6], P[0], [0.15, 0.85]], [P[1], P[2], [0.5]], [P[3], P[4], [0.5]],
              [P[4], P[5], [0.5]], [P[5], P[6], [0.3, 0.7]]];
    for (t = tramos) let (A = t[0], B = t[1], n = nrm(A, B))
        for (f = t[2]) translate(_pt_tramo(A, B, f) - n * montaje_a)
            circle(d = montaje_d, $fn = 32);
}

module mejilla_2d() sobre_suelo_2d() difference() { perfil_ext(); celosia_2d(); agujeros_montaje_2d(); }

module mejilla(z0) translate([0, 0, z0]) linear_extrude(piel_e) mejilla_2d();

// LOS DOS CACHETES SON LA MISMA PIEZA: la misma extrusion a los dos lados,
// asi que el patron se ve espejado de un lado al otro, como en el despiece
// (dos cachetes simetricos). Se imprime dos veces el mismo STL.
module mejillas() { mejilla(-piel_e); mejilla(ancho_total); }
module cachete() mejilla(0);          // uno solo, para imprimir

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

// LA CUBIERTA EN DOS MITADES, con solape. 580 mm de ancho no entran en una
// MJF de serie; se parte por el medio con un solape de `solape_l` de largo y
// medio espesor: la mitad A lleva la cara interior en el solape y la B la
// exterior. La costura queda en el medio del techo: cuando la cubierta tenga
// su forma drapeada, la costura se mueve a un pliegue (papel, sec.8).
solape_l = 12;
module _banda_solape_2d(exterior)
    sobre_suelo_2d()
        difference() {
            offset(r = exterior ? piel_e : piel_e/2) perfil_lateral();
            offset(r = exterior ? piel_e/2 : 0) perfil_lateral();
        }
module banda_mitad(cual) {
    zm = ancho_total / 2;
    difference() {
        banda();
        // lo que no es de esta mitad
        if (cual == "A") translate([-100, -100, zm + solape_l/2]) cube([700, 500, 700]);
        else             translate([-100, -100, zm - solape_l/2 - 700]) cube([700, 500, 700]);
        // la mitad del espesor que cede en el solape
        translate([0, 0, zm - solape_l/2 - 0.01])
            linear_extrude(solape_l + 0.02) _banda_solape_2d(cual == "A");
    }
}

// --- lo que sigue igual ---------------------------------------------------
// Los paneles van en STL propio: en el concepto son aluminio OSCURO dentro de
// la piel blanca, y ese contraste es la idea (panel duro en marco blando).
// Pintarlos del aluminio claro de render.py los funde con la piel.
module aluminio() { rails(); marcos_ventana(); costillas(); tapa_valle(); }
module acrilico() { piel_trasera(); }
module madera()   { bandeja_base(); paticas(); }

if      (PART == "mejillas") mejillas();
else if (PART == "cachete")  cachete();
else if (PART == "banda")    banda();
else if (PART == "banda_A")  banda_mitad("A");
else if (PART == "banda_B")  banda_mitad("B");
else if (PART == "aluminio") aluminio();
else if (PART == "paneles")  paneles();
else if (PART == "acrilico") acrilico();
else if (PART == "madera")   madera();
else if (PART == "todo")     { mejillas(); banda(); aluminio(); paneles(); acrilico(); madera(); }
else assert(false, str("PART desconocida: ", PART));

echo(str("PIEL: espesor ", piel_e, ", celosia de ", celosia_n, " nervios, marco ",
         celosia_marco, ", abierto ", celosia_abierto_mm2, " mm2 por cachete (",
         100*celosia_abierto, " % del perfil), respira ", celosia_abierto_ventana_mm2));
