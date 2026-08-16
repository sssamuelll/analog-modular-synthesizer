// coupon.scad — se corta ANTES que cualquier plancha (spec §3/§10).
// Escaleras de agujero para M3/M4/M5, ranura de tuerca T y probeta de
// canto/apriete. Marcar el kerf ganador en case/README.md.
include <params.scad>
paso = 12;
module escalera(ds, y) for (i = [0 : len(ds)-1])
    translate([8 + i*paso, y]) circle(d = ds[i]);   // sin kerf: se mide crudo
difference() {
    square([100, 62]);
    escalera([2.9, 3.0, 3.1, 3.2, 3.3, 3.4, 3.5], 12);   // M3
    escalera([4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6], 27);   // M4
    escalera([5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6], 42);   // M5
    translate([8, 52]) square([30, 6.2]);  // ranura perfil 2020
    translate([55, 50]) square([40, 8]);   // lengueta de probeta de apriete
}
