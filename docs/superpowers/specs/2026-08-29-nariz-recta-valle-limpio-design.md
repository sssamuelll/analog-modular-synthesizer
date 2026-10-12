# SAM17 — Nariz recta, meseta al pico, valle limpio

> **Enmienda 2026-10-11 (ficha 6):** la nariz sube hasta pisar 1 mm de la cara del riel de abajo (`retiro_placa_inf` 9 → 11.9, blank 545.62 × 53.10) y el retorno de la meseta baja de 4 a 9 hasta pisar la del riel de arriba (blank 593.02 × 78.85): las dos rendijas se cierran. La línea de sombra bajo y sobre el riel, y las reglas de `guarda_nariz()` (1 mm de aire bajo el riel) y `guarda_retorno_meseta()` (`holgura_rail` sobre él) que la pedían, eran del barrido de cuando las filas giraban. Lo mide `guarda_labio_chapas()` ([`2026-10-11-case-persiana-design.md`](2026-10-11-case-persiana-design.md) §7.3).

**Fecha:** 2026-08-29 · **Estado:** aprobado por Samuel en conversación (las tres
notas, y la esquina de abajo a 45° «y ya luego vemos cómo queda»); implementado en
la rama `feat/case-nariz-recta` con sus puertas ·
**Enmienda:** [`2026-08-15-case-design.md`](2026-08-15-case-design.md) (rev. 24),
[`2026-08-28-costilla-pletina-design.md`](2026-08-28-costilla-pletina-design.md) §10 y
[`2026-08-27-case-esqueleto-visible-design.md`](2026-08-27-case-esqueleto-visible-design.md)
(muere la bahía). **No toca** la silueta salvo sus esquinas, los ángulos, las
tres filas ni la trasera.

## 1. De dónde sale

Samuel abrió el case en Blender el 2026-08-29 — por primera vez con **cada pieza
como objeto con su nombre** (`renders/build/sam17-piezas.blend`) — y trajo tres
notas sobre el aluminio, con captura:

1. **La pieza que «encajona» el valle no va ahí**: en el valle solo van los dos
   Z-Rails del 1U. Esa pieza es la **bahía** (`bahia`), la bandeja de 60 mm bajo la
   fila 1U que la spec del 27-08 hizo tercer miembro y sitio del patch bay.
2. **Un embellecedor de aluminio en la sección inferior delantera**, que deja
   desnudo el Z-Rail. Y no curvo: *«en vez de una nariz curva, una nariz recta,
   TAL CUAL como el case que generé con Gemini»* — marcos laterales con la esquina
   de abajo cortada a 45° y una banda vertical de aluminio sobre la madera.
3. **Lo mismo en la sección superior**: el riel-eje de la fila de arriba asomaba en
   los 13 mm entre el canto del panel y la meseta.

## 2. Lo que se decidió, nota por nota

### 2.1 La bahía se va, sin heredero

Fuera la bandeja entera: suelo, dos alas, cuatro lengüetas, su retícula, sus dos
M4 en la placa del valle y su DXF. **Lo que hereda cada uno de sus trabajos:**

| trabajo de la bahía | quién lo hace ahora |
|---|---|
| tercer miembro, «ata las dos costillas en cortante» (spec 27-08 §4.2) | los seis rieles por sus placas de 6, la tabla debajo (bolted al canto de los anillos) y la trasera detrás. El racking del conjunto sigue siendo **#203** y se cierra cargando el prototipo, como antes |
| centrar la fila 1U en su boca | los dos rieles van **arrimados al frente de la ventana del valle** (`ventana_valle()`): el primero arranca donde acaba la banda, y entre banda y panel 1U queda el mismo labio de 2 mm que entre dos filas cualesquiera. Los 3 mm que ocupaban las dos alas sobran **detrás**, bajo el vuelo de la cara de arriba, donde no se ven |
| dar fondo a la placa del valle (recibía las lengüetas) | la placa del valle vuelve a `placa_fondo` = 26 como las otras dos, con el M3 de la pestaña de la banda y nada más |
| «apoyar» la banda del valle por su canto trasero | **nadie, y nunca lo hizo** — ver §7 |

El interior de la fila 1U queda abierto al case: los tiles cuelgan en el aire como
los módulos 3U, con 119 mm hasta la tabla. Es la regla del 17-08: *el interior es
para los módulos*.

### 2.2 La nariz recta

**La esquina del anillo cambia** (vértice 0 del perfil, frente-abajo): en vez de los
dos arcos que dejaba `radio_punta = 400` (9.5 abajo y 30.1 en el arranque de la
cara), un **chaflán a 45° de `chaflan_nariz` = 6 mm** sobre cada arista y un
**frente vertical de 13 mm** hasta el arranque de la cara de abajo. Debajo no hay
módulos que se coma, y se midió antes de elegirlo: la esquina más baja del riel del
frente está a 13.3 del suelo y su esquina más cercana a la nariz a x+y = 37.4; el
panel de abajo arranca a x+y = 39.2. Con 6 quedan 31.4 mm de aire hasta el riel.

**La pieza nueva es la `nariz`**: una banda de la misma chapa de 1.5 que los marcos
de la trasera, doblada sobre esa esquina — pie de 18 sobre la tabla, chaflán,
frente vertical y un tramo subiendo por la cara de abajo hasta **s = 10.27**, justo
debajo de la placa de anclaje —, atornillada a la **tabla** por el pie con **tres
M4 desde dentro**. Ningún tornillo en la cara vista. Desarrollo **540.32 × 47.38**,
tres dobleces (45°, 45° y 35°).

Dos consecuencias que no son gusto:

- **La placa de la cara de abajo se retira 9 mm más del arranque de la cara**
  (`retiro_placa_inf`): en las puntas placa y nariz viven en la misma rebanada de z,
  así que la banda acaba `hol_piel` por debajo de donde arranca la placa. Su tope lo
  pone el cajeado del riel del frente (1.5 D de canto): con 9 quedan 7.08 contra
  6.75.
- **La nariz se para debajo de la cara del riel, y queda una línea de sombra.** La
  fila de abajo es tapa (gira sobre el riel del valle) y al abrir la esquina honda
  del riel del frente **sale por la cara en s = 12.8**; la nariz es fija. Se queda
  en 10.27: 2.2 mm de aire más los 2 del labio del riel bajo el panel — lo mismo que
  se ve entre dos filas de cualquier Eurorack.

### 2.3 La meseta llega al pico, y dobla

No hay pieza nueva arriba: **la meseta del miembro trasero alto crece de 27.5 a
40.5** y llega al pico, y en el pico **dobla hacia abajo un retorno de 4 mm** por la
cara de arriba (`retorno_meseta`). `inset_remate_frente` muere.

> *Enmienda (la misma noche):* la meseta sigue hasta el **plano trasero** (50) y
> dobla ahí como banda; el marco de la trasera de la mañana desaparece y la tapa
> de arriba abre 180°. Ver `2026-08-29-marco-ventana-banda-estructural-design.md`.
> *Y más noche:* con el techo en chaflán (variante B) la meseta acaba a 6 del
> plano trasero y dobla 45° al chaflán y otros 45° a un labio de 18 — la nariz
> arriba y atrás. Ver `2026-08-29-trasera-capturada-talon-nariz-design.md` §5.

El inset llevaba escrito que era *«lo único que deja abrir la tapa de arriba»* con
una tabla medida (retiro 0 → abre 13.2°). Esos números son de cuando la meseta era
**acrílico de 8 apoyado en el riel**. Con la chapa de 1.5 la cara de abajo de la
meseta queda a 18.9 mm del eje y nada de lo que gira pasa de 16.2: se corrió
`guarda_tapa()` con la meseta en el pico **antes de tocar nada** y la fila de
arriba siguió abriendo **121.5°**, igual que hoy. El inset era un vestigio.

El retorno tampoco puede bajar lo que quiera: el canto alto del panel gira sobre el
M4 del riel con **16.18 mm de radio**, y a 1.5 bajo la cara ese círculo llega hasta
s = 149.4 de los 155 de la cara. Con 4 el retorno acaba en 151 y le sobran **0.80
mm radiales**. Queda una línea de sombra de **6 mm** sobre el panel (2 de labio + 4
de aire). Menos que eso solo lo da un listón mecanizado con la cara interior
cóncava y concéntrica al eje — como la tapa de un piano —, que no es esta pieza; se
juzga en render.

De regalo: el retorno mata la ola del canto libre de 528 mm y su canto vivo, que es
exactamente lo que hacía que **«la meseta se lea como repisa»** (Iris, §10 de la
spec del 28-08). Cerrado por construcción.

## 3. La regla de las esquinas: `radio_chapa`

Toda esquina del anillo que lleva chapa doblada encima mide el **radio exterior del
doblez de esa chapa**: `radio_chapa` = `radio_doblez_costilla` + `t_costilla` =
**4.5**. Son cinco esquinas: las dos del chaflán y el arranque de la cara de abajo
(la nariz), el pico (el retorno de la meseta) y la esquina trasera-alta (el marco de
la trasera). Mueren `radio_punta` (400) y `radio_remate` (2); `radio_trasero` = 0
se queda solo con la esquina trasera-baja, que no dobla nadie.

Por qué no es gusto: la chapa dobla con **su** radio, no con el del anillo, y una
esquina viva del anillo bajo un doblez a 90° **asoma 1.9 mm** por fuera de la chapa
(4.5 × (√2 − 1)); bajo uno a 45°, 0.4. La esquina trasera-alta lo tenía así desde el
29-08 por la mañana (marco a 4.5 sobre anillo a 0) y nadie lo vio en el render.

Lo que se pierde: `radio_remate` = 2 rimaba con el radio de esquina de panel del
#45. Pesa menos que 1.9 mm de esquina asomando. Y lo que cuesta: `placa_chaflan`
baja de 12 a **11** — el pico pasa de radio 2 a 4.5, la placa de arriba se retira
1.04 más de él y su cajeado del riel-eje se quedaba a 6.53 del corte contra 6.75.

## 4. Las puertas (escritas antes que el modelo, vistas en rojo)

| puerta | qué exige |
|---|---|
| `anillo_tiene_chaflan()` (check_dxf) | releído del DXF de la costilla: el punto más cercano a la esquina está sobre x+y = 6, hay frente a plomo desde el chaflán hasta el radio de arriba y suelo desde el chaflán. Con los arcos viejos fallaba por 0.44 mm y el frente medía cero |
| `guarda_nariz()` | `radio_chapa` es el radio del doblez; el chaflán deja frente (≥ 5) y libra el riel (≥ 5); ≥ 1 mm de aire bajo la cara del riel; **barrido**: la esquina del riel del frente sale por la cara ≥ 1.5 mm por encima de la nariz; los M4 del pie fuera del doblez y a 1.5 D del canto |
| `taladros_nariz()` (check_dxf) | los tres M4 en `nariz_2d` a 1.5 D del canto libre del pie, y los mismos tres en la tabla (`d_pie_tornillo`) |
| `guarda_retorno_meseta()` | la esquina interior del retorno queda ≥ 0.5 mm radiales fuera del círculo del canto del panel; el retorno acaba por encima de la cara del riel-eje. Imprime la línea de sombra |
| `guarda_remate()` | `prof_sup + t_piel + t_costilla == marco_remate`, y la meseta arranca exactamente en el pico |
| `guarda_fila_1u()` | la fila (33.65 + 10) cabe en `ventana_valle()`; imprime lo que sobra (3.00) |
| `guarda_tapa()` | el barrido de las dos filas con la nariz entera y el retorno como obstáculos: siguen 63.8° y 121.5° |
| `guarda_valle()` | **HUECO**, ver §7 |

`solapes()`, `alineacion()`, `apoyo()`, `guarda_anclajes()`, `cuerpos_dentro_del_anillo()`,
`taladros_placas()` y `taladros_reticula()` perdieron a la bahía y siguen verdes.

## 5. Lo que se ve

- **Frente:** de la tabla al panel de abajo todo es aluminio — pie, chaflán, frente,
  cara — con una línea de sombra de 4 mm bajo el panel (2 aire + 2 labio).
- **Techo:** la meseta va del marco de la trasera al pico sin canto vivo, y dobla
  sobre el panel de arriba con 6 mm de sombra.
- **Valle:** banda de 18.3, labio de 2, panel 1U, y nada debajo.
- **Esquinas:** el radio 4.5 hace que el chaflán se lea *suave* en 1.5 mm de
  6082-T6 (radio interior 3). Un chaflán *crisp* como el de la referencia —
  mecanizada, no plegada — pediría una aleación que doble a 0.5 t (5754 H22) y
  `radio_doblez_costilla` a 0.75. Se decide en render.

## 6. Lo que cambia para el taller de chapa

- **Entra `nariz_2d`**: desarrollo 540.32 × 47.38, tres dobleces, tres M4 en el pie.
- **`miembro_alto_2d` crece**: desarrollo 588.00 × 81.02 (era 64.9) — la meseta a
  40.5 y un cuarto doblez, el del retorno, a 45°.
- **Sale `bahia_2d`**, y con él cuatro M4 y dos roscas pasantes de la placa del valle.
- `placa_valle_2d` vuelve al fondo de 26; `placa_cara_inf_2d` se acorta 9 por delante.
- **`costilla_2d`** cambia de contorno en la nariz (chaflán + radios 4.5) y en las dos
  esquinas del techo (radio 4.5). El cupón (#237) no cambia: es la sección.
- Tornillería: 53 itemizados (eran 59: −4 lengüetas, −5 M3 fantasma de la banda a la
  bahía, +3 M4 de la nariz).

## 7. Lo que este documento NO cierra

- **La banda del valle no tiene apoyo, y ahora la puerta lo dice.** `guarda_valle()`
  medía un voladizo corto desde «el ala delantera de la bahía» — pero la banda
  acababa EN la cara exterior del ala y se tocaban en una arista, que no es un
  apoyo. Sin bahía el modelo honesto es la viga biapoyada entre pestañas: con 200 N
  en el centro **cede 213 mm y fluye a 27 N**. Es el mismo 27 N que el §10 de la spec
  del 28-08 tenía apuntado; ahora es un HUECO declarado (exit 2) en vez de un
  párrafo. Salidas, para decidir en render: (a) **rebajar 1.4 mm el canto trasero de
  la banda** para que apoye sobre el labio del primer riel 1U — es una pieza de 3 mm
  que puede ir al taller de mecanizado con los anillos —; (b) un retorno hacia
  abajo en ese mismo canto; (c) las dos.
- **`paso_horizontal` puede bajar 3 mm** (fondo −3): es lo que ocupaban las dos alas
  de la bahía y hoy sobra detrás de la fila 1U. Cambia la silueta y todos los
  números golden del papel; se propone, no se hace.
- **El chaflán suave** (§5): si en el render se lee blando, la palanca es la
  aleación de la chapa, no el modelo.
- **Racking del conjunto (#203)**, como siempre, y con un miembro menos que antes.
- **El cupón (#237)** sigue sin cortarse.

## 8. Enmiendas a otros papeles — ejecutadas en esta misma tanda

| papel | qué cambia |
|---|---|
| `2026-08-15-case-design.md` | rev. 24 en el historial; §11 sin cambios |
| `2026-08-28-costilla-pletina-design.md` §10 | «la meseta se lee como repisa» cerrado; «la banda fluye a ~27 N» pasa a HUECO de puerta con sus salidas |
| `2026-08-27-case-esqueleto-visible-design.md` | enmienda en cabecera: la bahía (§2 decisión 4, §5) muere el 2026-08-29 |
| `case/README.md` | nariz, meseta al pico, radios, bahía fuera, BOM, tornillería |
| `case/PLIEGO.md` | rev. 24: `nariz_2d` con sus líneas de plegado, `miembro_alto_2d` con el cuarto doblez, fuera `bahia_2d`, radios del anillo |
| `case/RFQ.md` | rev. 23: miembros ×2 + nariz; dobleces a 45° y 35° además del de 90° |
