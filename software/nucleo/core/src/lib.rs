#![cfg_attr(not(test), no_std)]
//! El contrato publico del SAM17.
//!
//! Spec: `docs/superpowers/specs/2026-08-17-nucleo-digital-design.md`.
//!
//! El invariante de §2.1 manda aqui: si una capacidad del instrumento no se
//! puede expresar con estos tipos y estos mensajes, no esta terminada.

pub mod atribucion;
pub mod descriptor;
pub mod descubrimiento;
pub mod j2;
pub mod medidas;
pub mod modelo;
pub mod param;
pub mod partes;
pub mod perturbacion;
pub mod pinout;
pub mod preset;
pub mod protocolo;
pub mod retencion;
pub mod servidor;
pub mod sysex;
pub mod usbmidi;
