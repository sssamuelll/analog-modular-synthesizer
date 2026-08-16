# Cajón y paneles

> **Sustituido**: el diseño vigente del case es la consola de dos pisos en
> acrílico (spec `docs/superpowers/specs/2026-08-15-case-design.md`, rev. 3;
> implementación en `case/`). Este documento queda como referencia de la
> tesis. Las convenciones de rotulación siguen vigentes y las hereda la
> plantilla `case/panels/`.

> Referencia: tesis, *Diseño y Construcción de Cajón y Paneles* (Gráficos
> 50–52).

## Objetivo

Albergar todos los módulos en una estructura mecánicamente sólida, con
acceso ergonómico a los controles y conectores, y espacio reservado para
expansión.

## Dimensiones

| Magnitud | Valor |
|----------|-------|
| Ancho | 950 mm |
| Altura | 440 mm |
| Profundidad | 100 – 200 mm |
| Altura panel | 19 cm (ajustable a raíles con tornillos) |
| Ancho panel | Variable según el módulo |

## Materiales

Ver Gráficos 50–52 de la tesis para el detalle de materiales y espesores
originales de este diseño. Quedaron sustituidos por el diseño vigente — ver
la nota de sustitución al inicio de este documento y
[`case/README.md`](../../case/README.md).

## Convenciones de diseño de paneles

- Distribución clara de entradas, salidas y controles.
- Etiquetas legibles para potenciómetros, jacks, LEDs y botones.
- Color y tipografía consistentes entre módulos.
- Numeración por orden lógico (no posición física): MIDI/CV, VCO, MIXER,
  VCF, ADSR, VCA.

## Mejoras propuestas

- Migrar a un **estándar Eurorack** (3U, 1HP = 5.08 mm) para
  intercambiabilidad con módulos comerciales.
- Generar planos en **DXF** o **SVG** para corte láser/CNC reproducible.
- Diseño de paneles en **KiCad** o **FrontPanelDesigner**.
- Soporte para iluminación LED del bus de alimentación.
- Tapa frontal opcional para transporte.
- Patas plegables o soporte inclinado.
