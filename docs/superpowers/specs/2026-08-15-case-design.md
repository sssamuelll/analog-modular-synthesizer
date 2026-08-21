# SAM17 — Diseño del case (consola de dos pisos en acrílico naranja)

**Fecha:** 2026-08-15
**Estado:** aprobado en diseño (rev. 3: pivote de cómputo, fuente v2 y
geometría del board de diseño), pendiente de plan de implementación
**Sustituye a:** formato de cajón de la tesis (madera 950 × 440 × 100–200 mm,
paneles galvanizados pintados) descrito en
[`docs/modules/08-case-panels.md`](../../modules/08-case-panels.md).
**Diseño de entrada:**
[`docs/architecture-poly.md`](../../architecture-poly.md) (4 voces con mandos
compartidos y circuitos replicados; dos caminos de señal; patch bay
normalizado); pivote de cómputo del PR #30 (el instrumento entero vive en un
RP2350, la computadora es externa y opcional); spec de la fuente v2
([`2026-08-16-psu-v2-goat-design.md`](2026-08-16-psu-v2-goat-design.md)).
**Render de intención aprobado:**
[`case/renders/propuesta-diseno-2026-08-16.png`](../../../case/renders/propuesta-diseno-2026-08-16.png)
(board del departamento de diseño, 2026-08-16 — manda sobre proporciones y
lenguaje visual).
**Gobernada por:** [`.specify/memory/constitution.md`](../../../.specify/memory/constitution.md).

> Historial de revisiones — **rev. 1**: consola inclinada de un piso, cheeks
> de madera, finger joints cementados, pantalla táctil de 7". **rev. 2**: todo
> acrílico, dos pisos, sándwich modernista con standoffs; muere la pantalla
> (interfaz = app web servida por el Pi). **rev. 3**: el cerebro pasa de
> Raspberry Pi 3B+ a **RP2350 con la computadora FUERA** — muere la app web
> servida por el Pi y el compañero pasa a ser un **plugin VST/CLAP** en la
> computadora del usuario; la fuente v2 fija los dominios de alimentación (y
> prevé WS2812); los ángulos quedan **medidos desde la vertical**, como los
> interpretó el board de diseño aprobado. **rev. 4** (2026-08-17/18): el
> panel pasa a **3U de EUROrack** (128.5 mm, 1 HP) y se compran Z-Rails de
> Tiptop de 104 HP — muere el formato propio de 190 mm y con él la
> proporción del board; el proceso pasa de **láser a fresado CNC** y `kerf`
> a 0; el zócalo se elimina; la pestaña de remate pasa a **junta pegada**;
> la bandeja de base sube a 8 mm y se vuelve portante. **rev. 5**
> (2026-08-21): la punta de arriba se lee **cuadrada** — `marco_remate` sube
> de 18 a 34 y los dos vértices del techo estrenan `radio_remate` = 2 en vez
> de compartir `radio_punta` —, el fondo crece 16 mm, y con eso la tapa de la
> fila de arriba pasa a abrir 180°. Muere de paso la idea de doblar la piel
> superior en cascada: no hace falta doblar nada. **rev. 6** (2026-08-21): la
> trasera deja de flotar y se **empotra** —mueren la junta de sombra y los 12
> separadores—, y entra el **octavo larguero** en la arista trasera-superior,
> que le da a la tapa de remate a qué atornillarse: se acabó la única junta
> pegada del case. `marco_remate` 34 → 42 y el fondo 291.2 → 299.2, que es lo
> que pide el barrido del Z-Rail para que la tapa siga abriendo 180°.
>
> **Aviso sobre el render de intención:** sigue mandando sobre lenguaje
> visual y proporciones *relativas*, pero **sus cotas están superadas**. Se
> dibujó para paneles de 190 mm y un case de 500 × 380 × 350; el case real
> mide **544.32 × 247.73 × 300.4**.

## 1. Objetivo

Diseñar y fabricar el case definitivo del SAM17 como pieza central del
instrumento: una **consola de dos pisos, íntegramente de acrílico naranja
translúcido**, de estilo modernista — placas planas, retícula estricta, cero
ornamento — unida por **separadores (standoffs) de aluminio a la vista** cuyo
ritmo de tornillería es parte del diseño. Los módulos cierran las dos caras
inclinadas con **paneles de PCB de aluminio**. Todo se fabrica por servicio de
**fresado CNC** a partir de archivos generados desde un modelo paramétrico
versionado en este repo. (Fue corte láser hasta el 2026-08-17; ver rev. 4.)

El case se dimensiona **por paneles, no por voces**: la arquitectura
polifónica fija que los mandos se comparten y los circuitos se replican, así
que el frontal no crece al crecer las voces — crece la PCB detrás de cada
panel. Se conservan de la tesis las convenciones de rotulación; **la altura de
panel de 190 mm NO se conservó** — desde el 2026-08-17 las dos filas son 3U
de EUROrack, 128.5 mm (rev. 4). El orden lógico es el de la cadena polifónica,
repartido en dos pisos por función:

- **Piso superior — generación:** MIDI/CV · VCO ×3
- **Piso inferior — procesamiento:** VCF · ADSR · VCA · MIXER

(El mixer va al final: en poly cada voz atraviesa su filtro y su VCA antes de
mezclarse.) El PSU vive dentro del piso inferior, sin panel propio más allá
de su zona de conexión trasera.

## 2. Decisiones de diseño

| Decisión | Elección | Por qué |
|---|---|---|
| Formato | Consola propia de dos pisos, **con paneles 3U de EUROrack** | La silueta es propia; el panel es estándar (128.5 mm, 1 HP = 5.08 mm). **Cambió el 2026-08-17**: antes eran 190 mm y explícitamente «no Eurorack». Se compraron Z-Rails de Tiptop de 104 HP |
| Estilo | Modernista: placas planas, retícula, standoffs vistos | Decisión estética del proyecto; el naranja translúcido hace el trabajo expresivo; el board de diseño aprobado fija el lenguaje |
| Estructura | Sándwich de placas de acrílico + esqueleto de perfiles 2020 + separadores de aluminio | La precisión depende solo de posiciones de agujero; elimina de raíz el problema de encajes |
| Paneles de módulo | PCB de aluminio (KiCad → fabricante tipo JLCPCB) | Serigrafía perfecta, agujeros exactos, acabado uniforme, bajo costo |
| Interfaz del módulo 2 | Instrumento autosuficiente en el RP2350; computadora **externa y opcional** por USB MIDI class-compliant + plugin compañero VST/CLAP. En el panel: **botón AFINAR + LED de estado**; los conectores de enlace (USB, MIDI DIN) los define el módulo 2 (panel o bloque trasero) | Pivote de cómputo del PR #30: si la computadora se cae en pleno concierto, el instrumento sigue sonando; desaparecen pantalla, Pi y sus consumos del frontal |
| Fabricación | **Fresado CNC** por servicio | El taller compensa el radio de herramienta en CAM, así que `kerf = 0`. El láser dejaba canto cónico en 8 mm y microfisuras en los bordes cargados. Cambió el 2026-08-17. Los DXF del repo siguen siendo directamente los archivos de corte |
| CAD | OpenSCAD paramétrico | Diseño-como-código versionable; exporta DXF (corte) y STL (render en Blender) |
| Servicio | **Enteramente desatornillable** + paneles de módulo desmontables | Acceso total al interior, sin una sola junta irreversible. Tuvo una **excepción única** hasta el 2026-08-21: la pestaña de remate iba PEGADA, porque el Z-Rail es extruido de pared fina de 1.2 mm y un M3 en esa cara atraviesa pared. La resolvió el **octavo larguero** — un 2020 en la arista trasera-superior que le da a esa tapa a qué atornillarse |

## 3. Postmortem del intento anterior (y cómo este diseño lo elimina)

El primer intento (adaptación del diseño de todbot, Thingiverse 3941263,
cortado en acrílico) falló porque **los dientes no cuadraron**. Causas raíz:

1. El diseño original está dibujado para plywood de **0.25 in = 6.35 mm**
   (fuente: README del autor en el zip); los dientes de un finger joint miden
   exactamente el espesor del material contrario. El acrílico se vende en
   espesores métricos y además el nominal trae tolerancia de fabricación
   (§11), así que todo diente quedaba corto o pasado.
2. Re-escalar el vector completo para compensar rompe el ancho de los dientes
   junto con las dimensiones generales.
3. El plywood comprime ~0.5 mm y perdona el ajuste a presión; el acrílico es
   rígido y frágil: o queda flojo o revienta.

La rev. 2+ no mitiga el problema: **lo elimina**. La arquitectura de sándwich
con standoffs no tiene encajes — la geometría crítica son posiciones y
diámetros de agujero, que no dependen del espesor de la plancha. Aun así:

- `t_acrilico` y `kerf` siguen siendo parámetros del modelo (afectan agujeros,
  largos de tornillo y estética de cantos).
- **Cupón de calibración** (`coupon.scad`) — **solo aplica si se vuelve al
  láser; con fresado `kerf = 0` y no hay nada que calibrar.** Pieza con una
  escalera de diámetros de agujero (ajuste deslizante y ajuste justo para
  M3/M4) y una probeta de canto. Se corta primero con el acrílico y la
  máquina reales, se fija el `kerf` medido, y solo entonces se cortan las
  planchas definitivas. Con láser habría que hacerlo **dos veces**, una por
  espesor: la franja no es la misma en 5 que en 8 mm.

## 4. Geometría (defaults; todo parametrizable)

Perfil lateral escalonado de consola de estudio erguida, como lo fijó el
board de diseño: piso inferior casi vertical frente al intérprete, piso
superior reclinado. **Los ángulos se miden desde la vertical** (convención
del board; la rev. 2 era ambigua y el departamento de diseño la resolvió en
esta dirección).

| Parámetro | Default | Nota |
|---|---|---|
| `ancho_total` | **544.32 mm** | DERIVADO del riel: 528.32 (104 HP) + 2 × `t_cheek`. Ya no lo fija la suma de módulos |
| `alto_panel_inf` / `_sup` | **128.5 mm** | 3U de EUROrack, las dos filas. Fue 190 hasta el 2026-08-17 |
| `sep_railes` | **122.5 mm** | Entre centros. Lo fija el PANEL (ranuras a 3.0 de cada canto), no el riel: el Z-Rail lleva pletina roscada continua |
| `angulo_inferior` | **35° desde la vertical** | Cara del piso de procesamiento |
| `angulo_superior` | **45° desde la vertical** | Cara del piso de generación |
| `alto_frontal` | **13 mm** | Canto delantero. **No es un zócalo**: el zócalo se eliminó |
| `fondo` / `alto_total` | derivados | **300.4 mm / 247.73 mm**. Ya NO cuadra con el board (350 × ~380): el board se dibujó para paneles de 190 |
| `t_acrilico` | 5 mm | Entrepiso, tapa del valle y las dos pieles. MEDIR con calibre (§11) |
| `t_base` / `t_cheek` | 8 mm | Suelo portante y costados. La bandeja de base subió de 5 a 8 al pasar a ser el propio canto de abajo |
| `kerf` | **0** | Correcto fresando: el CAM compensa el radio de herramienta. Solo vuelve a ser negativo si se regresa al láser |
| `n_bulkheads` | 2 | Costados exteriores; el modelo admite uno central si el vano lo pide |

Los valores derivados los calcula el modelo, no se fijan a mano. Las holguras
que deciden el diseño viven en **`case/clearance_budget.py`** (Principio II:
presupuesto ejecutable con aserciones, no prosa):

- altura interior del piso inferior vs. altura del transformador real del
  módulo 1 (según spec de la fuente v2), margen ≥ 15 mm;
- profundidad libre bajo cada cara vs. la PCB más honda del censo real de
  módulos — tras el pivote de cómputo el cerebro es un RP2350 y ninguna pieza
  domina de antemano, así que el censo se hace, no se supone;
- suma de anchos mínimos de panel + expansión vs. ancho útil, **por piso**;
- largo de standoffs vs. espesores reales de placas apiladas.

El script corre en verde **antes** de mandar nada a cortar (Principio III: la
comprobación va antes del paso destructivo).

## 5. Estructura

- **Costados (×2): acrílico naranja** de 8 mm (o laminado 2 × 4 mm), perfil
  escalonado de dos pisos. Son las piezas portantes: reciben los
  perfiles 2020 del esqueleto (raíles y largueros, tornillo M5 al alma) y
  los standoffs de las pieles.
- **Bandejas horizontales de acrílico** (base y entrepiso) atornilladas con
  tuercas T M3 a un **esqueleto de perfiles 2020** (los mismos del sistema de
  paneles: 8 largueros de esqueleto —2 de base, 2 de entrepiso, remate
  superior, repisa, valle y remate trasero— además de los 4 raíles de paneles; el
  reparto exacto lo fija `centros_esqueleto()` en el modelo). Un solo sistema
  de fijación para todo el instrumento; un standoff no puede sujetar una
  bandeja de 528 mm de vano.
- **Las placas de acrílico anclan solo a largueros de esqueleto**, nunca a los
  4 raíles de panel: esos van girados al ángulo de su cara, y un tornillo
  contra una cara inclinada entra descentrado y apoya la arandela de canto
  sobre acrílico frágil. Verificado por `alineacion()` en el budget.
- **Separadores (standoffs) de aluminio M4** (macho-hembra y hembra-hembra)
  con tornillería inox de botón: reservados a las pieles flotantes (junta de
  sombra de 5 mm) — la retícula visible y regular de puntos de unión es el
  ornamento permitido.
- **Piel trasera de acrílico por piso**, flotando en standoffs con junta de
  sombra (shadow gap) perimetral — desmontable, lleva la ventilación (§7).
- **Paneles de módulo: PCB de aluminio** de ancho variable en múltiplos de
  1 HP (5.08 mm), **128.5 mm de alto**, cerrando las dos caras inclinadas.
- **Pies de goma** bajo la base.
- Sin pegamento estructural salvo la pestaña de remate (ver §2).

## 6. Raíles y sistema de paneles

- **4 perfiles de aluminio 2020** (dos por piso, arriba y abajo de cada cara
  inclinada), atornillados a los costados.
- **Tuercas T deslizantes M3**: cada panel se atornilla en cualquier posición
  horizontal; los anchos de módulo pueden cambiar libremente durante el
  desarrollo.
- Tornillos de panel a **5 mm del borde** superior e inferior → separación
  entre centros de raíl = **180 mm** por piso. Offsets exactos raíl–panel los
  resuelve el modelo CAD.
- **El patch bay normalizado no pide sitio propio**: vive en los jacks de
  cada módulo (pin de switch del Thonkiconn), no en un módulo aparte — no se
  reserva zona de patch bay en el frontal. Sí infla el ancho de los paneles
  que ganan jacks; eso lo vigila el budget por piso.
- La plantilla KiCad de panel (en `case/panels/`) fija: **alto 128.5 mm**, posición
  de agujeros de tornillo, zona útil de componentes y estilo de serigrafía
  (tipografía y convenciones de `docs/modules/08-case-panels.md`, revisadas
  al lenguaje modernista: retícula, sin adornos).
- Requisitos derivados para el panel del módulo 2: **botón AFINAR + LED de
  estado**; los conectores de enlace con la computadora externa (USB MIDI
  class-compliant, MIDI DIN con opto) los ubica el diseño del módulo 2 — en
  su panel o en el bloque trasero fijo; el case solo garantiza el acceso.

## 7. Eléctrico y seguridad

- **Bloque trasero fijo del piso inferior** (esquina junto al costado
  derecho): entrada IEC C14 con portafusible + interruptor. El cableado de
  230 V vive solo en ese bloque y llega al transformador del módulo 1,
  montado sobre la base junto al costado derecho. **Las pieles removibles
  nunca llevan mains.**
- **Bonding de tierra** (requisito del módulo 1,
  [`design-notes.md` §13](../../../hardware/01-power-supply/notes/design-notes.md)):
  espárrago M4 único junto al PSU + cable verde/amarillo con terminal de ojal
  bajo un tornillo de cada panel de aluminio. Ni los raíles 2020 ni los
  standoffs anodizados cuentan como camino de tierra confiable.
- **Ventilación con firma**: las perforaciones de las pieles traseras y de la
  base (bajo el PSU) dibujan **onda sierra, triangular y cuadrada** — las
  tres formas de onda de los VCOs — trazadas como retícula geométrica
  estricta, coherente con el lenguaje modernista (así aparecen en la vista
  posterior del board). Convección natural para el PSU lineal.
- Requisito derivado hacia los módulos (no es trabajo del case): las PCBs
  llevan **conformal coating**, porque el cuerpo es deliberadamente abierto
  (juntas de sombra y ventilación).

## 8. Archivos y flujo de trabajo

```
case/
├── cad/          sam17_case.scad (modelo paramétrico)
│                 coupon.scad (cupón: escalera de agujeros + probeta de canto)
│                 export.ps1 / Makefile → regenera DXF + STL con un comando
├── plans/        DXF por plancha de acrílico, nesteados — salida directa
│                 al servicio de corte
├── panels/       plantilla KiCad de panel de aluminio
├── renders/      propuesta-diseno-2026-08-16.png (board aprobado, intención)
│                 STL → Blender (acrílico naranja translúcido, aluminio)
│                 → PNG del conjunto
├── clearance_budget.py   holguras del §4, ejecutable con aserciones
└── README.md     BOM de herrajes, orden de ensamblaje, procedimiento del
                  cupón, calibración de kerf
```

- Requiere instalar **OpenSCAD** (~50 MB); Blender e Inkscape ya están.
- **El artefacto es el script** (convención de la constitución): el `.scad` es
  la fuente de verdad y lo que se revisa en el PR; los DXF/STL se regeneran
  con el script de export y se commitean como artefactos de fabricación, igual
  que los gerbers en `hardware/*/fab/`.

## 9. BOM mecánico (categorías; cantidades exactas en implementación)

Standoffs de aluminio M4 de 5 mm (solo las pieles), tornillería inox M4 de
botón + arandelas (siempre arandela contra acrílico; **arandela ANCHA d16 en
los cuatro ejes de giro**, que con la d9 normal el acrílico fluye),
**4 Z-Rails de Tiptop de 104 HP** (528.32 mm, sección 23.8 × 10) + **7
largueros 2020 de 528.32 mm**, tuercas T M3 + tornillos M3 (25: las planchas
a los largueros), entrada IEC C14 con fusible e interruptor, espárrago M4 +
cable 1.5 mm² verde/amarillo + terminales de ojal (bonding), paticas
metálicas torneadas d16 × 8, tornillería del transformador, pasacables del
entrepiso, **16 tornillos M5 de botón** (2 por larguero 2020) y **8 M4** que
roscan en el propio Z-Rail — 4 de hombro con Belleville para los ejes, 4 de
mano para los cierres. **Sin adhesivo**: la tapa de remate dejó de ir pegada
el 2026-08-21.

Los perfiles van entre las caras internas de los costados, así que su largo es
el ancho útil (**528.32 mm**), **no `ancho_total`** (544.32 mm). Cantidades y largo:
salida real de `openscad -D 'PART=\"bom\"' case/cad/sam17_case.scad` — el
modelo las cuenta de `centros_rail()` + `centros_esqueleto()`, y quien las
recuente después de tocar `params.scad` toma ese eco, no este párrafo.

## 10. Verificación

1. **Cupón antes que planchas** — el kerf y los diámetros de ajuste medidos
   se registran en `case/README.md` junto con proveedor, material y máquina.
   **Con fresado esto se reduce a medir el espesor real de la plancha**, que
   sigue siendo obligatorio: el PMMA colado llega con tolerancia de hasta
   ±1.2 mm en 8 mm, y dos piezas están acotadas contra el espesor. Es la
   aplicación de los Principios III y V: la comprobación va antes del paso
   destructivo, y entre cortar a ciegas y no cortar, no se corta.
2. `case/clearance_budget.py` **en verde**, con autocomprobación del cálculo,
   aserciones que fallan si el diseño se sale, y bloque de lo que no cubre.
3. El script de export debe regenerar todos los DXF/STL sin errores desde un
   repo limpio, y **salir con código de error** si algo queda a medias.
4. Checklist de ensamblaje en `case/README.md` con el orden: costados →
   largueros 2020 → bandejas → raíles → tapa del valle → electricidad y
   bonding → pieles y pestaña → paticas y paneles.

   Este punto decía antes «costados → bandejas y standoffs → raíles», y era
   físicamente imposible según el §5 de esta misma spec: las bandejas se
   atornillan con tuercas T al esqueleto, y una tuerca T vive dentro de la
   ranura del perfil. Sin largueros no hay dónde atornillar la bandeja
   (issue #50). Además metía bandejas y pieles en el mismo paso, y no son el
   mismo herraje: las bandejas van con tuerca T al esqueleto, las pieles
   cuelgan de separadores M4 al final.

## 11. Lo que NO está confirmado

Convención del repo (Principio I): lo no verificado no se suaviza, se lista
con qué habría que medir para cerrarlo.

- **Espesor real del acrílico naranja**: el nominal miente. Y con PMMA
  **colado** (GS, que es el que pide el diseño por su baja tensión interna)
  la tolerancia llega a **±(0.4 + 0.1 × espesor)**, o sea ±1.2 mm en 8 mm —
  confirmado por escrito por Schaeffer AG el 2026-08-18: *«Die
  Herstellungstoleranzen können wir jedoch nicht beeinflussen»*. Nadie la
  mejora. Se cierra midiendo con calibre la plancha comprada y metiendo ese
  valor en `t_acrilico` / `t_base` / `t_cheek`, **antes de cortar**. El
  taller debe medir y avisar; es una de las preguntas del RFQ. Issue #98.
- ~~**Kerf**~~ — **CERRADO por cambio de proceso** (2026-08-17). Con fresado
  CNC el CAM compensa el radio de herramienta y la pieza sale a la cota del
  dibujo, así que `kerf = 0` y no hay nada que calibrar. El procedimiento del
  cupón se conserva en `case/README.md` por si se vuelve al láser — y
  entonces hay que hacerlo **dos veces**, una por espesor. Issue #40.

- **Qué cara del Z-Rail mira al panel**: la hoja de Tiptop acota el taladro
  M4 de punta a 9.5 mm de un canto y por tanto a 14.3 del otro; cuál de los
  dos toca el panel no está confirmado. Si fuera el otro, `rail_er_eje` pasa
  de 14.3 a 9.5 y hay que re-derivar. Se cierra con el riel en la mano y un
  calibrador. Issue #97.
- **Transformador y térmica de la fuente v2**: la spec de la fuente
  ([`2026-08-16-psu-v2-goat-design.md`](2026-08-16-psu-v2-goat-design.md))
  define pre-reg + LT3045/LT3094 y trae su propia lista de no confirmado; el
  budget del case toma de ahí la altura del transformador y la necesidad real
  de ventilación cuando esa spec cierre sus números.
- **Censo de fondos de PCB por módulo**: la aserción de profundidad usa
  estimados hasta que cada módulo publique su PCB (tras el pivote de cómputo
  ya no hay una pieza dominante conocida).
- **Suma de anchos de panel por piso vs. `ancho_total`**: solo cierra cuando
  cada panel esté dibujado; el budget la vigila con anchos mínimos estimados
  por módulo y por piso — y el patch bay normalizado añade jacks a varios
  paneles. Si un piso no cabe, `ancho_total` sube — es un parámetro, no una
  promesa.
- **Rigidez del vano a ~500 mm sin costado central**: heurística. Si el
  prototipo flexa, `n_bulkheads` pasa a 3 y se re-exporta; se cierra cargando
  el prototipo real.
- **Comportamiento del acrílico bajo apriete de standoffs**: el diseño manda
  arandela y agujero con holgura, pero el par máximo antes de fisura no está
  medido; se cierra con la probeta del cupón.

## 12. Fuera de alcance (el diseño no los bloquea)

Al cerrar la tanda se abren como issues con evidencia (Principio VI):

- **Plugin compañero VST/CLAP** (nih-plug, Rust) y todo el enlace con la
  computadora externa — software, flujo spec-kit, ya descrito en el pivote de
  cómputo del PR #30.
- Tapa frontal de transporte.
- Patas plegables / soporte de ángulo variable.
- **Iluminación WS2812**: la fuente v2 ya le reserva alimentación
  (+5 V digital con SMPS encapsulada para RP2350 + WS2812); el translúcido
  naranja la difunde. El case no la implementa en esta tanda, pero las
  bandejas dejan paso de cableado.
- Layouts individuales de cada panel de módulo (trabajo por módulo usando la
  plantilla de `case/panels/`).
