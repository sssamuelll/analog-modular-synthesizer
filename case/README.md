# Cajón y paneles

Diseños mecánicos del SAM17. Ver [`docs/modules/08-case-panels.md`](../docs/modules/08-case-panels.md)
para el detalle funcional, dimensiones y materiales.

## Estructura

```
case/
├── README.md
├── plans/        Planos de cajón en DXF/SVG (corte CNC o láser)
├── panels/       Paneles frontales por módulo (DXF/SVG, uno por módulo)
└── renders/      Renderizados 3D (FreeCAD/Blender/PNG) opcionales
```

## Estado

- [ ] Plano del cajón en formato vectorial
- [ ] Paneles individuales por módulo (1U / 3U según se decida)
- [ ] Render 3D del conjunto
- [ ] Lista de tornillería y herrajes
- [ ] **Bonding de tierra**: espárrago M4 único + un cable verde/amarillo por
      panel. El cajón es de madera, así que los paneles galvanizados no están
      unidos entre sí por la estructura y hay que bondarlos uno a uno. Requisito
      que impone el módulo 1 —
      [`hardware/01-power-supply/notes/design-notes.md`](../hardware/01-power-supply/notes/design-notes.md) §13
- [ ] Decisión: ¿estándar Eurorack o el formato personalizado de la tesis?
