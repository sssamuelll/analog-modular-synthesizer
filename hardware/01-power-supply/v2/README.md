# PSU v2 — Power Supply Module

**Estado:** Diseño completo; pendiente de mula y stock LCSC el día de mandar.

## Arquitectura

Cascada de **dos etapas reguladas por riel**:

- **Etapa 1 (pre-regulación):** LM2941CT (TO-220-5, +13.1 V) y LM2991T (−12.9 V)
  ajustan el valle del puente rectificador (~14 V) a voltajes intermedios,
  tolerando el rizado del bulk y acomodando el dropout del riel ultra-bajo-ruido
  que viene después.
  
- **Etapa 2 (regulación de precisión):** Parejas de LT3045/LT3094 en paralelo
  (×2 por riel, DFN-10/DFN-12) regulan a +12.000 V / −12.000 V exactos con ruido
  residual sub-milivoltio (LT3045: 8 µVrms típico; LT3094: 10 µVrms típico, 10 Hz–100 kHz).
  Cada pareja comparte red SET + ballast de 20 mΩ por chip para igualar corriente.

**Cifras de diseño:**
- Corriente: ±650 mA (±325 mA por chip en la pareja).
- Disipación térmica: ~0.33 W por chip LT, DFN pequeño con granja de vías EP.
- Rizado de salida: < 1 mV pico-pico @ ±650 mA (expectativa, §4-5 miden).
- Drift térmico: < ±50 ppm/°C (VREF del LT × tolerancia R_SET 1 %).

## Documentación

| Fuente | Contenido |
|---|---|
| [docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md](../../docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md) | Especificación funcional y margen de tolerancia |
| [docs/superpowers/plans/2026-08-16-psu-v2-goat.md](../../docs/superpowers/plans/2026-08-16-psu-v2-goat.md) | Plan de implementación (5 fases, tareas 6-10) |
| [notes/design-notes.md](notes/design-notes.md) | Datasheet gates (§1), stock (§2), decisiones (§3), medidas de la mula (§4), bring-up (§5) |
| [fab/README.md](fab/README.md) | Ficheros Gerber, BOM JLCPCB, puertas antes de fabricar |
| [kicad/](kicad/) | Esquemático y PCB (sam17-power-v2.kicad_sch / .kicad_pcb) |
| [pcb/renders/](pcb/renders/) | Screenshots 3D de la placa (anteproyecto visual) |

## Puertas abiertas (antes de pedir a JLCPCB)

1. **Medidas en la mula prototipo** (§4 design-notes): valle VRAW, pico en vacío,
   rizado real, térmica → fija los setpoints RV2/RV3. [Issue dedicada](../../issues).
   
2. **Re-verificar stock LCSC** (§2 design-notes): LT3045EDD/LT3094EDD (Extended,
   citadas 2026-08-16) + fallback 120 kΩ 1 % ±100 ppm. Códigos en `fab/bom-jlc.csv`.
   
3. **Rotaciones de DFN en JLCPCB** (fab/README.md): verificar miniaturas de
   ensamblaje para U4–U7 (DFN-10 y DFN-12 apaisados) — gotcha de KiCad ↔ JLC.

## ⚠ Advertencias de montaje

- **BR1 (puente rectificador):** la esquina `+` moldeada va a la cruz `+` del silk
  (pad 1). Girado 180° cabe igual y corta el puente.
  
- **U2 (LM2991T):** el tab **NO** está a masa, está a VRAW− (−20 V). Requiere mica
  y casquillo aislante obligatorios si comparte disipador con U1.
  
- **Vías del EP de U4-U7:** inspeccionar juntas tras reflow si no se pidió
  "Epoxy Filled & Capped" (riesgo de wicking de pasta).
