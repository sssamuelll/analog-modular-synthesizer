# Hardware — Módulo 6: ADSR

> Documentación funcional: [`docs/modules/06-adsr.md`](../../docs/modules/06-adsr.md).

## Resumen

Generador de envolvente ADSR con núcleo **ICM7555** (variante CMOS del 555)
en configuración monoestable y un capacitor cuya carga/descarga se rutea
por cuatro caminos diferentes según la etapa.

## Estructura del directorio

```
06-adsr/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — capturas de la envolvente en osciloscopio)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Capturas de envolvente para distintos valores A/D/S/R
- [ ] Medición de tiempos mínimos y máximos por etapa
- [ ] Evaluar duplicar el módulo (la spec final pide 2 envolventes)
