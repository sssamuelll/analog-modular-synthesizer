# Hardware — Módulo 4: Mixer

> [!IMPORTANT]
> **El SAM17 pasa a polifónico de 4 voces.** Este módulo **se mueve al final
> de la cadena**: ya no suma tres osciladores antes del filtro, suma **cuatro voces
> ya filtradas y con su VCA**.
>
> No es un detalle de orden: sumar antes del filtro sería parafónico, no polifónico.
> Es exactamente la diferencia entre los dos.
>
> Arquitectura completa: [`docs/architecture-poly.md`](../../docs/architecture-poly.md)


> Documentación funcional: [`docs/modules/04-mixer.md`](../../docs/modules/04-mixer.md).

## Resumen

Sumador inversor de 3 canales (TL074) con control de nivel por canal, salida
acoplada en DC (permite sumar CV además de audio).

## Estructura del directorio

```
04-mixer/
├── README.md
├── bom.csv
├── kicad/      (pendiente)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — pruebas de crosstalk y ruido)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Medición de SNR
- [ ] Evaluar variante AC-coupled seleccionable
