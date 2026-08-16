# PSU v2 — Power Supply Module

**Estado:** En diseño.

## Arquitectura

La fuente v2 es una cascada de dos etapas por riel: pre-regulador ajustable TO-220-5 (LM2941 → +13.1 V, LM2991 → −12.9 V) alimentando una pareja de LDO ultra-bajo-ruido en paralelo (LT3045 ×2 → +12.000 V, LT3094 ×2 → −12.000 V). Rieles sub-µV con pre-regulación y regulación de precisión.

Especificación completa: [docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md](../../docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md)

## ⚠ Advertencia

El silicio ultra no está congelado: §2 de [notes/design-notes.md](notes/design-notes.md) caduca el día de mandar.
