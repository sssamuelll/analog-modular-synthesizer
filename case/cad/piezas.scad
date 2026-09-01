// Cada pieza del case por separado y con su NOMBRE, para el .blend de
// identificacion (renders/piezas.py). Samuel senala una pieza en Blender, lee su
// nombre en el Outliner y ese nombre es el del repo -- se acabo adivinar de que
// pieza habla una captura.
//
//   openscad -o build/piezas/<nombre>.stl -D 'PIEZA="<nombre>"' piezas.scad
//
// No es un artefacto de fabricacion: no lo exporta export.ps1 ni lo lee ninguna
// puerta. Los nombres son los de los modulos de sam17_case.scad.
include <params.scad>
use <sam17_case.scad>
PIEZA = "anillos";
au = ancho_total - 2*t_anillo;             // gemela de ancho_util (use<> no la exporta)

module rieles_3u() {
    cr = centros_rail();
    angs = [angulo_inferior, angulo_inferior, angulo_superior, angulo_superior];
    for (i = [0 : 3])
        translate([cr[i].x, cr[i].y, ancho_total/2])
            rotate([0, 0, -angs[i]]) rotate([90, 0, 0]) rail_er(au - 2*t_placa);
}
module rieles_3u_reales_prototipo() {
    cr = centros_rail();
    angs = [angulo_inferior, angulo_inferior, angulo_superior, angulo_superior];
    for (i = [0 : 3])
        translate([cr[i].x, cr[i].y, ancho_total/2])
            rotate([0, 0, -angs[i]]) rotate([90, 0, 0])
                translate([rail_er_fondo/2 - rail_er_eje, 0, 0])
                    rail_er(au - 2*t_placa);
}
module rieles_1u() {
    for (c = centros_rail_1u())
        translate([c.x, c.y, ancho_total/2])
            rotate([0, 0, -90]) rotate([90, 0, 0])
                translate([rail_er_fondo/2 - rail_er_eje, 0, 0])
                    rail_er(au - 2*t_placa);
}
module rieles_1u_reales_prototipo() {
    rieles_1u();
}

if      (PIEZA == "anillos")           costillas();
else if (PIEZA == "rieles_3u")         rieles_3u();
else if (PIEZA == "rieles_3u_reales_prototipo") rieles_3u_reales_prototipo();
else if (PIEZA == "rieles_1u")         rieles_1u();
else if (PIEZA == "rieles_1u_reales_prototipo") rieles_1u_reales_prototipo();
else if (PIEZA == "paneles")           paneles();
else if (PIEZA == "marcos_ventana")    marcos_ventana();
else if (PIEZA == "nariz")             nariz();
else if (PIEZA == "talon")             talon();
else if (PIEZA == "miembro_alto")      miembro_alto();
else if (PIEZA == "tapa_valle")        tapa_valle();
else if (PIEZA == "tapa_valle_boca_prototipo") tapa_valle_boca_prototipo();
else if (PIEZA == "boca_visual_valle_prototipo") boca_visual_valle_prototipo();
else if (PIEZA == "soportes_boca_valle_prototipo") soportes_boca_valle_prototipo();
else if (PIEZA == "barrido_extraccion_boca_prototipo") barrido_extraccion_boca_prototipo();
else if (PIEZA == "barrido_extraccion_soportes_prototipo") barrido_extraccion_soportes_prototipo();
else if (PIEZA == "barrido_extraccion_paneles_prototipo") barrido_extraccion_paneles_prototipo();
else if (PIEZA == "cabezas_m3_boca_prototipo") cabezas_m3_boca_prototipo();
else if (PIEZA == "herramientas_m3_boca_prototipo") herramientas_m3_boca_prototipo();
else if (PIEZA == "tira_anti_ruido_valle") tira_anti_ruido_valle();
else if (PIEZA == "tiras_boca_valle_prototipo") tiras_boca_valle_prototipo();
else if (PIEZA == "costados")          costados();
else if (PIEZA == "piel_trasera")      piel_trasera();
else if (PIEZA == "tabla")             bandeja_base();
else if (PIEZA == "paticas")           paticas();
else if (PIEZA == "chasis")            chasis();
else assert(false, str("PIEZA desconocida: ", PIEZA));
