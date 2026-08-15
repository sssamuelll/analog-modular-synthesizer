# SAM17 — Diseño del case (consola inclinada de acrílico naranja)

**Fecha:** 2026-08-15
**Estado:** aprobado en diseño, pendiente de plan de implementación
**Sustituye a:** formato de cajón de la tesis (madera 950 × 440 × 100–200 mm,
paneles galvanizados pintados) descrito en
[`docs/modules/08-case-panels.md`](../../modules/08-case-panels.md).

## 1. Objetivo

Diseñar y fabricar el case definitivo del SAM17 como pieza central del
instrumento: una consola inclinada tipo skiff (silueta del case Eurorack de
Moog, escalada al SAM17) que mezcla tres materiales con roles claros —
**cheeks laterales de madera**, **cuerpo estructural de acrílico naranja
translúcido** y **paneles de módulo en PCB de aluminio**. Todo se fabrica por
servicios de corte láser/CNC a partir de archivos generados desde un modelo
paramétrico versionado en este repo.

No es una reproducción fiel del cajón de la tesis: es la evolución "obra de
arte" prevista en la sección *Mejoras propuestas* del módulo 8. Se conservan
del original: ancho total 950 mm, altura de panel 190 mm, orden lógico de
módulos y las convenciones de rotulación.

## 2. Decisiones de diseño

| Decisión | Elección | Por qué |
|---|---|---|
| Formato | Consola propia (no Eurorack 3U) | Los módulos de la tesis usan paneles de 190 mm; migrar a 3U obligaría a rediseñar todos los layouts y PCBs |
| Geometría | Cuña inclinada tipo skiff Moog | Ergonomía, silueta escultural, referencia estética elegida |
| Estructura | Acrílico naranja translúcido estructural + cheeks de madera | El acrílico es el cuerpo visible ("no completamente cerrado": el interior brilla a través); la madera aporta rigidez en los extremos y el acabado cálido |
| Paneles de módulo | PCB de aluminio (KiCad → fabricante tipo JLCPCB) | Serigrafía perfecta para rótulos, agujeros exactos, acabado uniforme, bajo costo; reemplaza la lámina galvanizada pintada a mano |
| Fabricación | Corte láser (acrílico) + CNC (madera) por servicio | Precisión de encajes; los DXF del repo son directamente los archivos de corte |
| CAD | OpenSCAD paramétrico | Diseño-como-código versionable; exporta DXF (corte) y STL (render en Blender); espesor y kerf son parámetros de entrada |
| Uniones acrílico–acrílico | Finger joints cementados con solvente | Unión química tipo acuario, look limpio, máxima resistencia |
| Uniones acrílico–madera | Tornillos M4 en insertos roscados | Los cheeks abrazan el monocasco; nada de dientes contra madera |
| Servicio | Tapa trasera atornillada + paneles de módulo desmontables | Acceso al PSU/bus board sin desarmar; los paneles son la "tapa" de la cara inclinada |

## 3. Postmortem del intento anterior (y cómo este diseño lo evita)

El primer intento (adaptación del diseño de todbot, Thingiverse 3941263,
cortado en acrílico) falló porque **los dientes no cuadraron**. Causas raíz:

1. El diseño original está dibujado para plywood de **0.25 in = 6.35 mm**;
   los dientes de un finger joint miden exactamente el espesor del material
   contrario. El acrílico se vende en espesores métricos (el "6 mm" real mide
   5.6–5.9 mm), así que todo diente quedaba corto o pasado.
2. Re-escalar el vector completo para compensar rompe el ancho de los dientes
   junto con las dimensiones generales.
3. El plywood comprime ~0.5 mm y perdona el ajuste a presión; el acrílico es
   rígido y frágil: o queda flojo o revienta. Un encaje pensado para madera
   no se transfiere a acrílico sin recalcular la holgura.

Mitigaciones obligatorias en este diseño:

- **Modelo paramétrico**: `t_acrilico`, `t_madera` y `kerf` son variables;
  toda la geometría de dientes y ranuras se genera desde ellas. Cambiar de
  proveedor o espesor = cambiar un número y re-exportar.
- **Cupón de calibración** (`coupon.scad`): pieza de prueba (~5 min de láser)
  con tres pares diente/ranura a distintos ajustes de kerf. Se corta primero
  con el acrílico y la máquina reales, se elige el ajuste que encaja firme
  sin forzar, se fija ese `kerf` en el modelo y solo entonces se cortan las
  planchas definitivas. **Prohibido cortar planchas sin cupón previo.**

## 4. Geometría (defaults; todo parametrizable)

Perfil lateral: trapecio rectángulo con la cara inclinada hacia el intérprete.

| Parámetro | Default | Nota |
|---|---|---|
| `ancho_total` | 950 mm | Como la tesis; se valida contra la suma de anchos de módulos + expansión |
| `angulo` | 14° | Inclinación de la cara de paneles |
| `alto_frontal` | 60 mm | Pared frontal (exterior) |
| `alto_panel` | 190 mm | Altura de panel de la tesis, se conserva |
| `fondo` | ~210 mm | Derivado: proyección de la cara inclinada + paredes |
| `alto_trasero` | ~110 mm | Derivado: `alto_frontal` + seno del ángulo × cara |
| `t_acrilico` | 5 mm | Decidir con el proveedor del acrílico naranja; el modelo se recalcula |
| `t_madera` | 18 mm | Cheeks |
| `kerf` | 0.2 mm | Se calibra con el cupón, nunca se asume |
| `n_costillas` | 2 | Divide el vano en 3 bahías (~300 mm cada una) |

Los valores derivados los calcula el modelo, no se fijan a mano. Verificación
dimensional obligatoria en implementación: la altura interior trasera debe
superar la altura del transformador real del módulo 1 con margen ≥ 15 mm, y
la profundidad libre bajo paneles debe aceptar el módulo más profundo
(MIDI/CV con Raspberry Pi 3B+ sobre separadores).

## 5. Estructura

- **Cheeks (×2): madera maciza** (haya o roble según disponibilidad del
  servicio CNC, acabado al aceite), 18 mm, perfil trapezoidal completo.
  Llevan los insertos roscados M4 donde atornilla el cuerpo de acrílico, los
  raíles y la tapa trasera.
- **Cuerpo de acrílico naranja translúcido** (base, pared frontal, pared
  trasera fija parcial — ver §7) unido con finger joints cementados, más la
  **tapa trasera removible** (también acrílico, atornillada a insertos en los
  cheeks).
- **Costillas internas (×2) de acrílico**, mismo perfil interior, cementadas
  a la base con encaje ranura-lengüeta. Sin ellas, 950 mm de vano comba.
  Soportan los raíles a mitad de vano y sirven de anclaje del bus board.
- **Paneles de módulo: PCB de aluminio** de ancho variable por módulo,
  190 mm de alto, cerrando la cara inclinada.
- **Pies de goma** atornillados a la base (la inclinación ya está en la
  geometría, no en las patas).

## 6. Raíles y sistema de paneles

- **2 perfiles de aluminio 2020** (extrusión estándar de impresora 3D) de
  950 mm, arriba y abajo de la cara inclinada, atornillados a los cheeks y
  apoyados en las costillas.
- **Tuercas T deslizantes M3**: cada panel se atornilla en cualquier posición
  horizontal, sin grilla de agujeros pretaladrada. Los anchos de módulo
  pueden cambiar libremente durante el desarrollo.
- Tornillos de panel a **5 mm del borde** superior e inferior → separación
  entre centros de raíl = **180 mm**. Los offsets exactos raíl–panel los
  resuelve el modelo CAD.
- La plantilla KiCad de panel (en `case/panels/`) fija: alto 190 mm, posición
  de agujeros de tornillo, zona útil de componentes y estilo de serigrafía
  (tipografía y convenciones de `docs/modules/08-case-panels.md`).

## 7. Eléctrico y seguridad

- **Bloque trasero fijo** (esquina junto al cheek derecho): entrada IEC C14
  con portafusible + interruptor. El cableado de 230 V vive solo en ese
  bloque y llega al transformador del módulo 1, montado en la base junto al
  cheek derecho. **La tapa removible nunca lleva mains.**
- **Bonding de tierra** (requisito del módulo 1,
  [`design-notes.md` §13](../../../hardware/01-power-supply/notes/design-notes.md)):
  espárrago M4 único junto al PSU + cable verde/amarillo con terminal de ojal
  bajo un tornillo de cada panel de aluminio. Los raíles 2020 anodizados
  **no** cuentan como camino de tierra confiable.
- **Ventilación con firma**: rejillas de la tapa trasera y de la base (bajo
  el PSU) cortadas con forma de **onda sierra, triangular y cuadrada** — las
  tres formas de onda de los VCOs. Convección natural para el PSU lineal.
- Requisito derivado hacia los módulos (no es trabajo del case): las PCBs
  llevan **conformal coating**, porque el cuerpo es deliberadamente abierto
  (ranuras decorativas y de ventilación).

## 8. Archivos y flujo de trabajo

```
case/
├── cad/          sam17_case.scad (modelo paramétrico)
│                 coupon.scad (cupón de calibración de kerf)
│                 export.ps1 / Makefile → regenera DXF + STL con un comando
├── plans/        DXF por plancha: acrílico (planchas nesteadas), cheeks
│                 madera, tapa trasera — salida directa al servicio de corte
├── panels/       plantilla KiCad de panel de aluminio
├── renders/      STL → Blender (materiales: acrílico naranja translúcido,
│                 madera aceitada, aluminio) → PNG del conjunto
└── README.md     BOM de herrajes, orden de ensamblaje, procedimiento del
                  cupón, calibración de kerf
```

- Requiere instalar **OpenSCAD** (~50 MB); Blender e Inkscape ya están.
- Los DXF exportados se versionan junto al `.scad` que los generó.

## 9. BOM mecánico (categorías; cantidades exactas en implementación)

Perfiles 2020 × 950 mm (×2), tuercas T M3 + tornillos M3×8 (paneles),
insertos roscados M4 para madera + tornillos M4 avellanados (cuerpo, raíles,
tapa), cemento solvente para acrílico (tipo Weld-On 4 / diclorometano),
entrada IEC C14 con fusible e interruptor, espárrago M4 + cable 1.5 mm²
verde/amarillo + terminales de ojal (bonding), pies de goma, tornillería del
transformador.

## 10. Verificación

1. **Cupón antes que planchas** — el kerf medido se registra en
   `case/README.md` junto con proveedor, material y máquina.
2. El script de export debe regenerar todos los DXF/STL sin errores desde un
   repo limpio (ese es el "test" del modelo).
3. Chequeo dimensional del §4 (transformador y módulo más profundo) contra
   medidas reales antes de mandar a cortar.
4. Checklist de ensamblaje en `case/README.md` con el orden: cementado del
   monocasco → insertos en cheeks → atornillado de cheeks → raíles →
   electricidad y bonding → tapa → paneles.

## 11. Fuera de alcance (issues futuros, el diseño no los bloquea)

- Tapa frontal de transporte.
- Patas plegables / soporte de ángulo variable.
- Iluminación LED dedicada del bus (el translúcido ya deja pasar la luz de
  los LEDs existentes).
- Layouts individuales de cada panel de módulo (trabajo por módulo usando la
  plantilla de `case/panels/`).
