//! El modelo de host de las seis ranuras del J2 (papel v3, §5.2 h; #444).
//!
//! El entorno del simulador de la junta del 2026-10-17 (`sim/junta3`, de Halberg) sobre la
//! maquina, la politica y los buzones REALES de `core`: el tic, el planificador, la
//! recuperacion, el GPDMA1, P0, P2 y el reloj del tic. **Modela, no mide**: lo que sale de aqui
//! lleva (S) en los papeles. Las candidatas K1 (presupuesto de escaladas), K3 y K4 (`sucia` y la
//! identidad en la maquina) y K5 (el supervisor) todavia no estan: el modelo hace lo que hace
//! hoy `fw/src/j2_tic.rs`.

pub mod fuzz;
pub mod motor;
