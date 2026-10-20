#![no_std]

//! La biblioteca del firmware del cerebro: lo que comparten `main.rs` y los
//! binarios del banco (`src/bin/`). Capa DELGADA a proposito, igual que
//! `main.rs`: lo que merezca un test vive en `sam17-nucleo-core`.

pub mod carga;
pub mod j2_banco;
pub mod j2_ejecutor;
pub mod j2_esclavo;
#[cfg(feature = "transporte-isr")]
pub mod j2_isr;
pub mod j2_spi;
#[cfg(feature = "transporte-tic")]
pub mod j2_tic;
#[cfg(feature = "j2-tcm")]
pub mod j2_tcm;
pub mod mpu;
#[cfg(feature = "muestreo")]
pub mod muestreo;
pub mod perfil;
pub mod reinicio;
#[cfg(feature = "secciones")]
pub mod secciones;
pub mod usb;
