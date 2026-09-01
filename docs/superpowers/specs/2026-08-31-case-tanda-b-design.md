# Tanda B del case: valle apoyado, fila auxiliar de 55 mm y paneles rehundidos

**Fecha:** 2026-08-31
**Estado:** aprobado para implementación
**Alcance:** case paramétrico, puertas/canarios, DXF, renders, Blender y papeles de taller.

## 1. Decisiones

Samuel aprueba las tres decisiones siguientes como una sola tanda:

1. La fila del valle pasa de 39.65 a **55.00 mm**. Ya no se presenta como Intellijel 1U: es la **fila auxiliar KONDOR de 55 mm**, compatible en ancho/HP y herraje con los otros Z-Rails, pero no compatible en altura ni separación vertical con Intellijel 1U.
2. La banda del valle gana un apoyo continuo y real sobre el primer Z-Rail de la fila auxiliar, sin tornillos visibles nuevos.
3. Los paneles de las tres filas quedan **rehundidos 1.50 mm** respecto de la silueta. Panel y sus dos rieles se mueven juntos; el contacto panel–riel no se separa.

La banda alta de la trasera no forma parte de esta tanda. Sigue como HUECO declarado: cerrarla exige una decisión visual y un render específico, no es una dependencia geométrica de estas tres decisiones.

## 2. Fila auxiliar KONDOR de 55 mm

- `alto_panel_1u`: 39.65 → **55.00**. Se conserva el nombre solo donde cambiarlo rompería interfaces de exportación; los textos y documentación dejan de llamarla Intellijel.
- El primer riel queda donde está: su cara delantera sigue naciendo en `ventana_valle()[0]`.
- Solo se mueve el segundo riel. La separación entre centros sigue derivada: `alto_panel_1u - 2*inset_er` = **49.00 mm**.
- `paso_horizontal`: 58.47 → **70.82** para que la ventana crezca 12.35 mm y conserve el margen previo. Cada milímetro añadido aquí suma un milímetro al fondo.
- Fondo nominal esperado: **319.76 mm** (la puerta debe derivarlo, no congelarlo como fuente geométrica).
- La puerta deja de exigir igualdad con `S_1U_INTELLIJEL = 33.65`. Debe exigir y publicar:
  - separación KONDOR = 49.00;
  - separación ≥ Intellijel, sin afirmar compatibilidad;
  - ventana suficiente para `separación + rail_er_alto`;
  - primer riel invariante ante la mutación 39.65 ↔ 55, medido contra la
    envolvente estática del panel fijo; no contra la antigua cota de barrido;
  - segundo riel desplazado exactamente 15.35 mm;
  - ancho/HP igual al de las filas 3U.

## 3. Apoyo real de la banda del valle

### 3.1 Geometría

La banda actual acaba en la cara delantera del primer Z-Rail y solo lo toca por una arista. Se convierte ese borde en un apoyo de superficie:

- la banda se prolonga **2.00 mm** hacia atrás, hasta el canto del panel auxiliar, a su espesor completo de 3.00 mm;
- el rehundido posterior del panel baja la cara del primer Z-Rail a 3.10 mm del plano: una banda de 3.00 no puede fabricar monolíticamente esos 0.10 mm restantes;
- una tira anti-ruido oculta de **0.20 mm nominal** trabaja comprimida **0.10 mm** y llena el gap real de 0.10 mm en toda la longitud útil;
- la línea visible conserva la lectura «banda + labio de 2 mm + panel»; el labio ahora pertenece a la banda y tiene función estructural;
- no entra ningún tornillo visible; la única adición es la tira oculta, consumible de montaje.

El DXF incorpora los 2.00 mm de prolongación a espesor completo. No hay rebaje ciego ni segunda operación de mecanizado. El 3D representa la tira ya comprimida en su gap de 0.10 mm.

### 3.2 Camino de carga

Una mano en el centro deja de cruzar 525 mm entre las dos pestañas. La carga baja por una tira de contacto de 50 mm, recorre como máximo el vuelo delantero entre el pico y el riel, entra en el Z-Rail y de ahí en las dos placas/marcos laterales.

`guarda_valle()` pasa de HUECO a assert. Modela conservadoramente una tira en voladizo de ancho `B_MANO`, largo del vuelo delantero, espesor `t_valle`, con 200 N en el borde. Debe exigir:

- tensión ≤ `RP02_ALUMINIO`;
- flecha ≤ `flecha_costado_max`;
- apoyo horizontal positivo y al menos 2.00 mm;
- gap entre banda y riel igual a `rehundido_panel + t_panel - t_valle` = 0.10 mm;
- espesor comprimido de la tira igual al gap y compresión nominal igual a 0.10 mm;
- solape completo en Z entre banda, tira y primer Z-Rail;
- el apoyo no invade el panel ni altera la posición del primer riel.

Canarios obligatorios: apoyo 0, tira ausente, compresión incorrecta y desplazamiento del primer riel deben fallar por el motivo correcto.

## 4. Paneles rehundidos 1.50 mm

Entra el parámetro explícito `rehundido_panel = 1.50`.

- En las dos filas 3U, el centro de cada Z-Rail se desplaza 1.50 mm hacia el interior siguiendo la normal local de la cara.
- En la fila auxiliar horizontal, ambos rieles bajan 1.50 mm.
- Los tres paneles se desplazan exactamente lo mismo; su dorso continúa apoyando en la cara exterior de los rieles.
- Los paneles son caras fijas y desmontables por tornillos; no existen ejes de giro. No se inventa un separador entre panel y riel.
- El anillo y el marco no se mueven: forman el borde visible de 1.50 mm.

Puertas y canarios obligatorios:

- rehundido real de cada cara = `rehundido_panel`;
- distancia dorso de panel–cara de riel = 0;
- riel y panel comparten el mismo desplazamiento normal;
- la ventana se dimensiona con la envolvente estática del riel cerrado; ninguna puerta depende de barridos ni ángulos de apertura;
- mutar `rehundido_panel` sin mover rieles o sin mover paneles falla;
- `solapes()`, cuerpos dentro del anillo y cajeados siguen verdes.

## 5. Orden de implementación (RED → GREEN)

1. Escribir puertas/canarios de la fila de 55 y observar el fallo contra 39.65/58.47.
2. Cambiar altura, semántica y valle; volver a verde.
3. Escribir puerta/canarios del apoyo y observar el HUECO/fallo actual.
4. Añadir prolongación y apoyo 3D/DXF; convertir `guarda_valle()` en assert y volver a verde.
5. Escribir puerta/canarios del rehundido y observar el fallo con paneles a ras.
6. Mover rieles y paneles juntos; ejecutar colisiones estáticas y resolver únicamente las dependencias demostradas por puertas.
7. Regenerar artefactos y papeles; ejecutar la suite completa y mutaciones.

## 6. Artefactos y papeles afectados

Como mínimo:

- `case/cad/params.scad`
- `case/cad/sam17_case.scad`
- `case/clearance_budget.py`
- `case/check_dxf.py`
- script de exportación y composición de Blender que ya use el repo
- `case/dxf/tapa_valle_2d.dxf` y cualquier DXF cuya silueta cambie por `paso_horizontal`
- STL/render/Blender del ensamblado
- `case/README.md`, `case/PLIEGO.md`, `case/RFQ.md`
- historial de `docs/superpowers/specs/2026-08-15-case-design.md`

Los números de bbox, masa, BOM y tornillería se derivan de la salida real. No se copian los valores previos si la regeneración los cambia.

## 7. Criterio de cierre

La tanda termina solo cuando:

- `clearance_budget.py` sale sin ROJO; el código 2 solo puede corresponder a HUECOS previos y ajenos a esta tanda;
- `check_dxf.py` sale 0 sobre DXF recién exportados;
- todos los canarios de estas tres decisiones demuestran fallo bajo mutación;
- OpenSCAD regenera los STL/DXF sin error nuevo;
- los renders muestran el labio apoyado, la fila de 55 y la sombra de 1.5;
- el `.blend` definitivo se abre y se comprueba visualmente;
- revisión independiente no encuentra un bloqueo;
- branch y PR contienen código, artefactos y papeles sincronizados.
