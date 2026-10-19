#![cfg_attr(not(test), no_std)]
//! El contrato publico del SAM17.
//!
//! Spec: `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`.
//!
//! El invariante de §2.1 manda aqui: si una capacidad del instrumento no se
//! puede expresar con estos tipos y estos mensajes, no esta terminada.

pub mod atribucion;
pub mod bahia;
pub mod bahia_serie;
pub mod buzones_j2;
pub mod descriptor;
pub mod descubrimiento;
pub mod envolvente;
pub mod escaladas_j2;
pub mod escritor;
pub mod fuerza;
pub mod j2;
pub mod maestro_j2;
pub mod marcos_j2;
pub mod medidas;
pub mod memoria;
pub mod modelo;
pub mod param;
pub mod partes;
pub mod perturbacion;
pub mod pinout;
pub mod politica;
pub mod preset;
pub mod protocolo;
pub mod rampa;
pub mod rejilla;
pub mod reloj;
pub mod retencion;
pub mod servidor;
pub mod supervisor_j2;
pub mod sysex;
pub mod tiempo_params;
pub mod transporte_j2;
pub mod usbmidi;
