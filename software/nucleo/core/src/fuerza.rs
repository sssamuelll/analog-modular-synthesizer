//! Fuerza de `Note On/Off` normalizada a 16 bits.
//!
//! `M2-115-U MIDI 2.0 Bit Scaling and Resolution v1.0.2`, §3.1, establece
//! que `Note On/Off Velocity` usa el escalado Min-Center-Max. Su §3.3.1
//! define el algoritmo aplicado aqui para convertir de 7 a 16 bits.

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug, Default)]
pub struct Fuerza(pub u16);

impl Fuerza {
    /// Convierte un byte MIDI 1.0, enmascarado primero a sus 7 bits validos.
    pub fn desde_midi1(v7: u8) -> Fuerza {
        let src_val = u32::from(v7 & 0x7F);
        let src_bits: u8 = 7;
        let dst_bits: u8 = 16;

        let scale_bits = dst_bits - src_bits;
        let src_center = 1u32 << (src_bits - 1);
        let mut bit_shifted_value = src_val << scale_bits;
        if src_val <= src_center {
            return Fuerza(bit_shifted_value as u16);
        }

        let repeat_bits = src_bits - 1;
        let repeat_mask = (1u32 << repeat_bits) - 1;
        let mut repeat_value = src_val & repeat_mask;
        if scale_bits > repeat_bits {
            repeat_value <<= scale_bits - repeat_bits;
        } else {
            repeat_value >>= repeat_bits - scale_bits;
        }
        while repeat_value != 0 {
            bit_shifted_value |= repeat_value;
            repeat_value >>= repeat_bits;
        }

        Fuerza(bit_shifted_value as u16)
    }
}
