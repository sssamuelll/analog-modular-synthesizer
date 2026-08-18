# PSU v2 — Power Supply Module

**Estado:** Diseño completo; pendiente solo de las comprobaciones del día de mandar
(stock LCSC y rotaciones de DFN).

> **La v1 no se construye** (decisión 2026-08-17). Era la mula contra la que se
> iban a congelar los setpoints; se va directo a la v2 y los setpoints se ajustan
> en sitio con RV2/RV3 durante el bring-up. Eso quita la puerta que bloqueaba el
> pedido, y mete una condición nueva al bring-up: **medir el valle de VRAW contra
> el umbral de 13.46 V** ([notes §4.1](notes/design-notes.md)) antes de dar la
> placa por buena. La v1 queda como diseño documentado, no como hardware.

## Arquitectura

Cascada de **dos etapas reguladas por riel**:

- **Etapa 1 (pre-regulación):** LM2941CT (TO-220-5, +13.1 V) y LM2991T (−12.9 V)
  ajustan el valle del puente rectificador (~14 V) a voltajes intermedios,
  tolerando el rizado del bulk y acomodando el dropout del riel ultra-bajo-ruido
  que viene después.
  
- **Etapa 2 (regulación de precisión):** Parejas de LT3045/LT3094 en paralelo
  (×2 por riel, DFN-10/DFN-12) con ruido residual objetivo:
  **0.8 µVrms (10 Hz–100 kHz)** — cifra de datasheet con el layout de la nota de
  aplicación; no se presume hasta medir con el LNA (spec §11.7).
  «Precisión» aquí es **ruido y PSRR, no exactitud absoluta**: `V_OUT = I_SET ×
  R_SET` sin trim, y el I_SET del propio chip es ±2 % garantizado sobre el rango
  de operación (DS p.3), así que el riel es **±12.0 V nominales, ±3 % peor caso**
  ([notes §2.6.1](notes/design-notes.md)). Donde este repo diga «12.000 V
  exactos», léase eso.
  Cada pareja comparte red SET + ballast de 20 mΩ por chip para igualar corriente.

**Cifras de diseño:**
- Corriente: ±650 mA (±325 mA por chip en la pareja).
- Disipación térmica: ~0.33 W por chip LT, DFN pequeño con granja de vías EP.
- Rizado de salida: < 1 mV pico-pico @ ±650 mA (expectativa, §4-5 miden).
- Exactitud de VOUT: **±3 % peor caso** (I_SET ±2 % del chip × R_SET ±1 %).
- Drift térmico de VOUT: **~100 ppm/°C (1.2 mV/°C)** por el R_SET (C114524).
  El 0,1 %/25 ppm se evaluó y **se descartó** el 2026-08-17: llevaría la ventana
  de ±3 % a ±2,1 % porque el término que manda es el chip, no el resistor
  ([notes §2.6.1](notes/design-notes.md)).

## Documentación

| Fuente | Contenido |
|---|---|
| [docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md](../../docs/superpowers/specs/2026-08-16-psu-v2-goat-design.md) | Especificación funcional y margen de tolerancia |
| [docs/superpowers/plans/2026-08-16-psu-v2-goat.md](../../docs/superpowers/plans/2026-08-16-psu-v2-goat.md) | Plan de implementación (5 fases, tareas 6-10) |
| [notes/design-notes.md](notes/design-notes.md) | Datasheet gates (§1), stock (§2), decisiones (§3), campaña de medidas + umbral de aborto (§4/§4.1), bring-up (§5) |
| [fab/README.md](fab/README.md) | Ficheros Gerber, BOM JLCPCB, puertas antes de fabricar |
| [kicad/](kicad/) | Esquemático y PCB (sam17-power-v2.kicad_sch / .kicad_pcb) |
| [pcb/](pcb/) | Screenshots 3D de la placa (anteproyecto visual) |

## Puertas abiertas (antes de pedir a JLCPCB)

1. ~~**Re-verificar stock LCSC**~~ — **CERRADA 2026-08-17** ([notes §2.6](notes/design-notes.md)):
   los 10 códigos del BOM de ensamblaje consultados en vivo, valor y package
   confirmados en ficha, los 10 con stock. El más fino es el shunt `C6920584`
   (1.000 u., 4 por placa). Re-mirar solo ese si pasa tiempo hasta el pedido.
   
2. **Rotaciones de DFN en JLCPCB** (fab/README.md): verificar miniaturas de
   ensamblaje para U4–U7 (DFN-10 y DFN-12 apaisados) — gotcha de KiCad ↔ JLC.
   **Es la única puerta que queda, y se cierra dentro del propio pedido.**

~~3. Medidas en la mula prototipo~~ — **cerrada por decisión, no por medida**: la
v1 no se construye. Los setpoints RV2/RV3 se fijan en el bring-up sobre la propia
v2 (§5 paso 5), y el criterio de aborto es el valle contra 13.46 V (§4.1).

## ⚠ Advertencias de montaje

- **BR1 (puente rectificador):** la esquina `+` moldeada va a la cruz `+` del silk
  (pad 1). Girado 180° cabe igual y corta el puente.
  
- **U2 (LM2991T):** el tab **NO** está a masa, está a VRAW− (−20 V). Requiere mica
  y casquillo aislante obligatorios si comparte disipador con U1.
  
- **Vías del EP de U4-U7:** inspeccionar juntas tras reflow si no se pidió
  "Epoxy Filled & Capped" (riesgo de wicking de pasta).
