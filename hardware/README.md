# Hardware

Esquemáticos, PCBs y BOMs para los 7 módulos del SAM17.

| Módulo | Carpeta | Documentación |
|--------|---------|---------------|
| 1 — Alimentación | [`01-power-supply/`](01-power-supply) | [`docs/modules/01-power-supply.md`](../docs/modules/01-power-supply.md) |
| 2 — MIDI/CV | [`02-midi-cv/`](02-midi-cv) | [`docs/modules/02-midi-cv.md`](../docs/modules/02-midi-cv.md) |
| 3 — VCO | [`03-vco/`](03-vco) | [`docs/modules/03-vco.md`](../docs/modules/03-vco.md) |
| 4 — Mixer | [`04-mixer/`](04-mixer) | [`docs/modules/04-mixer.md`](../docs/modules/04-mixer.md) |
| 5 — VCF | [`05-vcf/`](05-vcf) | [`docs/modules/05-vcf.md`](../docs/modules/05-vcf.md) |
| 6 — ADSR | [`06-adsr/`](06-adsr) | [`docs/modules/06-adsr.md`](../docs/modules/06-adsr.md) |
| 7 — VCA | [`07-vca/`](07-vca) | [`docs/modules/07-vca.md`](../docs/modules/07-vca.md) |

## Estructura por módulo

Cada subdirectorio sigue la misma convención:

```
NN-<módulo>/
├── README.md            Resumen, especificaciones y mejoras
├── kicad/               Proyecto KiCad (.kicad_pro, .kicad_sch, .kicad_pcb)
├── schematics/          Esquemáticos exportados a PDF
├── pcb/                 Renderizados PCB (PNG/SVG/3D)
├── bom.csv              Lista de materiales
└── notes/               Notas de diseño, mediciones, calibración
```

## Convenciones eléctricas

Ver [`docs/architecture.md`](../docs/architecture.md) para el detalle del bus
de alimentación, niveles de señal y estándar 1 V/octava compartido por
todos los módulos.

## Estado actual

Este es el esqueleto inicial: los proyectos KiCad, esquemáticos y PCBs
todavía no están versionados. Las BOM contienen una **versión preliminar**
extraída de la tesis (Tabla 8 y 9 de la evaluación económica). Si vas a
empezar a capturar el esquemático de un módulo, abre primero un *issue*
para evitar trabajo duplicado.
