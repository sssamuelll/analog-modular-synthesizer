// coupon.scad — se corta ANTES que cualquier plancha (spec §3/§10).
// Escaleras de agujero para M3/M4/M5, ranura de tuerca T y probeta de
// canto/apriete. Marcar el kerf ganador en case/README.md.
//
// TODO el cupon se dibuja CRUDO, sin kerf: es la pieza que MIDE el kerf,
// aplicarselo seria circular. Los peldanos son diametros DIBUJADOS.
//
// Cada escalera va de (diametro nominal del tornillo - 0.5) a (+0.5) en
// pasos de 0.1 — el mismo rango de kerf fisico que acepta el assert de
// clearance_budget.py, para que CUALQUIER kerf que el budget de por bueno
// se pueda medir en esta pieza. Ronda final: antes arrancaban en el nominal
// (2.9/4.0/5.0) y con un canal real de 0.1 mm o mas el agujero FISICO mas
// chico de la escalera M3 ya salia por encima de 3.0: el "entra firme sin
// forzar" del paso 2 del README no existia en el cupon y el kerf no se
// podia medir con el.
include <params.scad>
paso = 12;
n = 11;                    // peldanos por escalera: -0.5 .. +0.5 en 0.1
ancho = 8*2 + (n-1)*paso;  // 136: la escalera manda el tamano del cupon
module escalera(d0, y) for (i = [0 : n-1])
    translate([8 + i*paso, y]) circle(d = d0 + i*0.1);
difference() {
    square([ancho, 62]);
    escalera(2.5, 12);                     // M3: 2.5 .. 3.5
    escalera(3.5, 27);                     // M4: 3.5 .. 4.5
    escalera(4.5, 42);                     // M5: 4.5 .. 5.5
    translate([8, 52]) square([30, 6.2]);  // ranura perfil 2020
    translate([55, 50]) square([40, 8]);   // lengueta de probeta de apriete
}
