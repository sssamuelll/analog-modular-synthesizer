// params.scad — unica fuente de verdad dimensional del case.
// Unidades: mm y grados. Angulos de cara MEDIDOS DESDE LA VERTICAL
// (convencion del board de diseno, spec §4 rev. 3).
// clearance_budget.py parsea este fichero: solo lineas `nombre = valor;`
// con valores numericos. No usar expresiones en este fichero.

// --- silueta (spec §4 + board 350 x ~380) ---
ancho_total     = 500;   // spec §4
alto_panel      = 190;   // spec §4, altura de panel de la tesis
angulo_inferior = 12;    // desde la vertical, cara de procesamiento
angulo_superior = 35;    // desde la vertical, cara de generacion
alto_frontal    = 50;    // zocalo delantero
prof_inferior   = 350;   // board: PROFUNDIDAD TOTAL
prof_superior   = 250;   // board: cota 250 del alzado lateral
paso_horizontal = 20;    // repisa entre cara inferior y superior

// --- materiales ---
t_acrilico = 5;    // planchas del cuerpo; MEDIR con calibre (spec §11)
t_cheek    = 8;    // costados portantes
t_panel    = 1.6;  // PCB de aluminio, espesor estandar JLCPCB
kerf       = 0.2;  // default; SE CALIBRA con el cupon (spec §11)

// --- sistema de paneles (spec §6) ---
rail            = 20;   // perfil 2020
inset_tornillo  = 5;    // tornillo de panel a 5 mm del borde
sep_railes      = 180;  // centros de rail por piso = 190 - 2*5
holgura_rail    = 4;    // separacion minima entre railes vecinos (fix solapes)

// --- esqueleto y herrajes ---
n_bulkheads      = 2;    // costados exteriores (3 si el vano flexa, spec §11)
d_M3_paso   = 3.4;  // agujero paso M3 (ISO holgura media)
d_M4_paso   = 4.5;  // agujero paso M4
d_M5_paso   = 5.5;  // agujero paso M5 (railes 2020 roscados en el alma)
gap_sombra  = 5;    // junta de sombra de las pieles flotantes
alto_pie    = 8;    // pie de goma bajo la base

// --- ventilacion con firma (spec §7) ---
vent_ancho_ranura = 4;   // ancho de la ranura-onda
vent_puente_min   = 4;   // puente minimo entre ranuras (fragilidad)
vent_periodo      = 40;  // periodo horizontal de cada onda

// --- lo que el budget vigila (spec §11: catalogos, no medidos) ---
alto_transformador  = 45;  // CATALOGO, no confirmado; medir pieza real
margen_transformador = 15; // spec §4
fondo_pcb_max       = 60;  // censo estimado de PCB mas honda, no confirmado
