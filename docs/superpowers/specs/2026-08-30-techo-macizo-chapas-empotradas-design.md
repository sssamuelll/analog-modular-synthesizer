# El techo macizo, con la salida de aire por el alero, y las tres chapas empotradas en el anillo

**Fecha:** 2026-08-30 · **Estado:** aprobado por Samuel en conversación («dale»)
sobre la propuesta de esta mañana, con sus cuatro números (chapa rehundida 1,
rebaje en las tres chapas; y para la tanda B, panel 1U de 55 y paneles 1.5
abajo) · **Tanda A de dos**: la B (la fila 1U más alta con sus rieles, los
paneles empotrados y el apoyo de la banda del valle) tiene su propia spec ·
**Supersede** en el techo, en la unión chapa-anillo y en la ventilación a la
spec del 29-08 (trasera capturada) y a la del 27-08 (esqueleto visible) en lo
que dicen de eso.

## 1. De dónde sale

Samuel, con el `.blend` de piezas abierto (cada pieza con el nombre de su módulo),
el 30-08 por la mañana:

> «en la pieza miembro alto no me gustan los huecos. es una decisión errática del
> diseño ya que esa parte es sensible a que le entren líquidos. lo otro es que el
> acabado debe sentirse perfecto con respecto a la esquina. perfectamente
> alineado con el del marco o si no se ve feo. tiene que ser una pieza que se
> sienta empotrada.»

Y, preguntado por la esquina de arriba-atrás, dos cosas y no una: **el borde de la
chapa contra el anillo** (termina a tope contra la cara interior y se le ve la
costura; empotrada = que entre en un rebaje del anillo, como el acrílico en su
bolsillo) y **el chaflán de la chapa no sigue el del anillo** (los dos dobleces a
45° con radio no se leen como el mismo plano que el chaflán de 6 mecanizado).
Sobre el acabado, su vara: «a pesar de que estoy haciendo el instrumento de forma
artesanal, tenga un acabado de instrumento profesional serio, así nivel Moog».

Tres hechos del repo que mandan aquí (trazados el 30-08; las citas van a línea):

1. Las 16 ranuras de la meseta son la **salida** del circuito de convección
   natural, no un adorno: entrada por la rejilla baja de la trasera (46 ranuras,
   7 193 mm² a y = 47), salida por la meseta (852 mm² a y = 255) y por las dos
   ondas abiertas de la trasera (2 289 mm² a y = 98). `guarda_aire()` exige salto
   térmico ≤ 15 K, no paridad de áreas; hoy da **10.8 K** con 6.33 W. Solo
   borrarlas: **15.9 K**, rojo (`params.scad` ~1612-1654; `clearance_budget.py`
   `guarda_aire`, `_rejilla_valle`, `_ondas_trasera`).
2. La chapa va **a ras** del contorno del anillo: el `.scad` usa los puntos del
   perfil como cara exterior y pone el espesor hacia dentro (`tramo_chapa()`),
   y termina **a tope** contra la cara interior (`z0 = t_anillo`). El único
   rebaje del anillo es para el acrílico (`rebaje_anillo` 6, `rehundido_acrilico`
   3). Ninguna puerta mide asiento, luz ni escalón de la chapa contra el anillo,
   y el sólido de la chapa se dibuja sin los arcos del plegado: la coincidencia
   de los dos chaflanes es coplanar sobre el papel y depende del taller en la
   pieza.
3. El presupuesto térmico cuenta **6.33 W** (solo los reguladores del PSU) y la
   spec de la fuente calcula **9.22 W** de peor caso para su chasis (a media
   carga, con el LED al tope del #104; `2026-08-18-fuente-chasis-telemetria.md`
   §3.1). No hay enlace ejecutable entre los dos. Con 9.22 W el diseño de hoy
   queda en **13.9 K**: por un pelo, y pasar por un pelo no es pasar.

## 2. La cuenta

Fórmula de `guarda_aire()`, tal cual (tiro de chimenea laminar, entrada y salida
en serie, C_D 0.65, 20 °C):

| escenario | salida (mm²) | tiro (mm) | ΔT a 6.33 W | ΔT a 9.22 W |
|---|---|---|---|---|
| hoy: meseta 852 + ondas 2 289 | 3 141 | 94 | 10.8 K | 13.9 K |
| techo macizo, nada más | 2 289 | 51 | **15.9 K** | 20.4 K |
| techo macizo + **rendija del alero** a 2.5, ocho tacos de 15 | 3 341 | 95 | **10.4 K** | **13.3 K** |
| ídem, seis tacos | 3 416 | 97 | 10.2 K | 13.1 K |
| ídem, rendija a 3.0 | 3 551 | 101 | 9.8 K | 12.6 K |

La rendija del alero (§3.2) está más alta que el centro de las ondas y aporta
más área que la meseta que sustituye: el aparato respira **mejor** que hoy en los
dos supuestos de potencia. Se adopta la fila en negrita: 2.5 es el aire que ya
hay entre el labio y la trasera, y los tacos son la misma junta de EPDM de 2.5
cortada a trozos.

## 3. El techo macizo, y la salida de aire por el alero

### 3.1 Lo que se quita

Las 16 ranuras de la meseta (`meseta_paso_hp`, `meseta_largo_ranura`, el bucle de
`miembro_alto_2d()` y `ranura_meseta_3d()`). La meseta queda **maciza**: un
líquido sobre el techo no tiene por dónde entrar. `_rejilla_valle()` deja de
existir como término de salida y `guarda_puentes_ventilacion()` pierde su caso
«meseta».

### 3.2 La rendija: lo que el labio ya tapa

El labio trasero del techo (18, de y = 250.18 a 232.18) tapa **6.5 mm** del canto
de arriba de la trasera (y1 = 238.68), y la trasera va **4 mm detrás del plano
trasero** (labio del bolsillo 3 + junta de asiento 1). Entre la cara interior del
labio y la cara vista de la plancha hay hoy **2.5 mm de aire** (`aire_labios`),
que la spec del 29-08 dejaba para una tira continua de EPDM. Por dentro, sobre el
canto de la trasera, quedan **13 mm** hasta la cara interior del chaflán.

Eso es una salida de aire hecha: el aire de la caja pasa por encima del canto de
la trasera y sale hacia **abajo** por la rendija, tapada por el alero del techo.
Un derrame sobre la meseta baja por el chaflán, por el labio, y gotea por el
canto del labio **4 mm por delante** de la plancha. Área: (541 − tacos) × 2.5 =
**1 052 mm²** con ocho tacos de 15, a y ≈ 238.

Con la chapa rehundida 1 (§4) la cara interior del labio pasa de 1.5 a 2.5 del
plano trasero. Para que la rendija siga midiendo 2.5, **la trasera retrocede el
mismo milímetro**: `rehundido_trasera = rehundido_acrilico + rehundido_chapa =
4` (su cara vista a 5 del plano). Es la única cota de la trasera que deja de ser
«la del costado, girada»: la junta de 1 y el hondo de 6 siguen iguales.

### 3.3 La junta a tacos, en los dos labios

La tira continua de 2.5 tras los labios (spec 29-08 §9, «con la primera pieza»)
se decide aquí: **tacos de EPDM de 2.5 × 15**, ocho por labio (uno cada ~65 mm,
pegados a la cara interior del labio), en el labio del techo **y** en el del
talón. Una sola regla para las dos juntas; sujetan la plancha sin que suene y
dejan la rendija libre entre ellos. Solo la de arriba se cuenta como salida. La
de abajo (a y ≈ 6-19, bajo el labio del talón, mirando al suelo) es una entrada
que no se cuenta: si entra algo de aire por ahí, mejora el tiro y no aparece en
el número.

### 3.4 Los 9.22 W

`potencia_disipada` pasa de 6.33 a **9.22 W**, con la cita: es el peor caso de la
spec de la fuente para su chasis (a media carga, no a 650 mA). Sigue sin incluir
la disipación de los módulos, que no está en ningún presupuesto del repo, y por
eso el techo se queda en 15 K y no pegado al número: 13.3 K deja 1.7 K.

### 3.5 El gotero

El canto libre del labio del techo puede llevar un **dobladillo** (un pliegue de
180°, 3 mm) que rompa el goteo por capilaridad hacia su cara interior. No se
dibuja en esta tanda: se decide con la primera pieza, mirando cómo gotea (§8).

## 4. Las tres chapas empotradas en el anillo

### 4.1 El rebaje de chapa

En la cara interior de cada anillo, a lo largo de todo el contorno donde hay
chapa (nariz: pie, chaflán y frente hasta P1; techo: del retorno de P4 por la
meseta, el chaflán de P5 y el labio hasta y = 232.18; talón: labio, chaflán y
pie), un **rebaje de `rebaje_chapa` = 3 de fondo** (z, 2 t, medido desde la
cara interior) y de `rehundido_chapa` a `rehundido_acrilico` en u (de 1 a 3 del
contorno). La chapa entra en él:

- su cara exterior queda a **`rehundido_chapa` = 1** por dentro del contorno del
  anillo, y su cara interior a 2.5; al suelo del rebaje (u = 3) le sobran 0.5:
  el suelo no posiciona, posicionan la brida y los M4 de los pies;
- su canto queda **debajo de 3 mm de anillo**, con `hol_piel` = 0.15 a la pared
  del rebaje: las tres chapas crecen **2 × (3 − 0.15) = 5.7 de ancho** (540.32 →
  546.02 entre paredes de rebaje);
- el borde del anillo es un **reborde de 1 × 3** (u = 0..1, z = 11..14) que
  recorre el contorno: es lo que se ve como marco, y lo que tapa el canto.

El acabado que Samuel pide sale de que ninguna de las dos cotas que se ven
depende del taller de chapa: la junta de sombra de 1 mm la fresa el anillo, y el
canto de la chapa no se ve. Un desvío de ±0.3 en el desarrollo o en el doblez se
esconde bajo el reborde, donde antes era un escalón sobre la superficie.

### 4.2 Las esquinas: el reborde sigue al pliegue

Hoy el anillo lleva `radio_chapa` = 4.5 (radio interior 3 + t) en las esquinas
que llevan chapa a 90° y en los dos vértices de cada chaflán: la esquina viva
asomaría 1.9 mm bajo un doblez de 90° y 0.4 bajo uno de 45°. Con la chapa
rehundida 1, el contorno del anillo es la cara exterior de la chapa desplazada
1 hacia fuera: **`radio_borde` = `radio_chapa` + `rehundido_chapa` = 5.5**,
concéntrico con el arco exterior del pliegue. En P5 (B), el chaflán de 6 del
anillo y el de la chapa quedan a 1 mm uno de otro y paralelos, con los vértices
redondeados sobre el mismo centro que el doblez: se leen como el mismo plano
aunque el taller doble a 2.9 o a 3.1, porque la diferencia cae dentro de la
junta de sombra y no sobre una arista compartida.

El sólido de la chapa se dibuja igual que hoy (cubos y polígonos, sin arcos); lo
que cambia es que el anillo ya no pretende coincidir con un arco que el modelo
no tiene.

### 4.3 El tramo trasero: presupuesto de franja

En el tramo P5-P6 el anillo lleva, además, el bolsillo de la trasera y el del
costado, y el rebaje de chapa se suma. De fuera a dentro (u desde el plano
trasero), con z desde la cara vista del anillo (cara interior en z = 14):

| u | z = 11..14 (los 3 del rebaje) | z = 8..11 | z < 8 |
|---|---|---|---|
| 0..1 | **reborde** | labio del bolsillo | macizo |
| 1..4 | rebaje de chapa (la chapa en 1..2.5, aire 2.5..4) | labio del bolsillo | macizo |
| 4..15 | **bolsillo de la trasera** (rebaje y bolsillo se funden: un solo vaciado de u = 1 a 15) | bolsillo de la trasera | macizo |
| 15..18 | pared (`pared_rebaje_trasera` = 3) | pared | macizo |
| 18..21 | bolsillo del costado (entra 3, como hoy) | ídem | macizo |

Dos cosas salen de la tabla: el **labio del bolsillo de la trasera baja de 6 a 3
de hondo** (z = 8..11; en z = 11..14 lo sustituyen el reborde y el propio labio
de la chapa, que a 2.5 de aire sigue parando la plancha hacia fuera), y **la
franja del tramo trasero pasa de 20 a 21** (`cara_anillo_trasera`) para que el
costado siga entrando 3 con su pared de 3. La alternativa que la spec del 29-08
ya dejaba a Samuel — el costado a 6 en los cuatro tramos — vale 24 aquí y se
sigue viendo 4 más ancho desde el lado; no se toma en esta tanda.

No queda ninguna aleta: el suelo del rebaje (u = 3 en los demás tramos) es aquí
la pared exterior del bolsillo (u = 4), y en los 3 mm del rebaje se vacía de
corrido. Lo vigila `guarda_rebaje_chapa()` (§6): ninguna pared del anillo por
debajo de `pared_rebaje_trasera`.

### 4.4 Las bridas del techo

Siguen **en la cara del anillo** — lo que `params.scad` llama no negociable: a
z ≥ t_anillo + t_placa está el barrido del panel de arriba —, pero como el labio
entra 3 en el rebaje, la brida dobla en z = 11 y apoya en un **cajeado de 3 de
fondo** con su huella (27 × 14.5 + `hol_piel` por lado), es decir, **1.5 por
debajo** de la cara interior. Los dos M4 ciegos se roscan desde el suelo del
cajeado (quedan 11 de pletina). La muesca del marco de la ventana sobre la
huella de la brida se queda: las cabezas siguen asomando.

### 4.5 El marco de la ventana

Su canto exterior se retira bajo las chapas `t_costilla` + `hol_piel` = 1.65
hoy; pasa a **`rehundido_chapa` + `t_costilla` + `hol_piel` = 2.65** en frente,
suelo, meseta y cola bajo el retorno. En el tramo trasero, donde va retirado
`t_piel` + `t_costilla` + tol + 0.5 detrás de la trasera y el labio, se retira
**1 más** (el labio entra 1 y la trasera también): la pata trasera del marco
pierde 1 de ancho, y `guarda_marco()` decide si los 28 de hoy (110 MPa contra
130) siguen valiendo o entra 29.

### 4.6 Nariz y talón

Mismo rebaje, mismo reborde, mismos radios: sus pies siguen atornillados a la
tabla con sus M4 (nada cambia en la tabla), y sus chaflanes y frentes entran en
el rebaje por los dos lados. Sin bridas: no hay cajeados nuevos por ellas. El
chaflán de la arista de abajo-fuera de la trasera (5.5) se recalcula con la
plancha 1 más adentro y el labio del bolsillo a 4 (`chaflan_trasera_bajo()` y su
gemela): es una cuenta, no una decisión.

## 5. Lo que se ve

Desde atrás: el mismo marco de metal a ras por los cuatro lados de la spec del
29-08 — dos cantos de anillo y dos labios de chapa —, pero ahora **los labios
están 1 mm por dentro de los cantos**, con una junta de sombra de 1 que los
recorre, y la trasera 5 mm adentro. Desde arriba: la meseta **lisa**, sin una
ranura, con su reborde de anillo de 1 alrededor y el chaflán de la esquina
siguiendo el doblez. Desde delante y desde el lado, lo mismo en la nariz y en el
talón: tres chapas dentro de dos marcos. Bajo el alero de atrás, nada que se
vea: la rendija mira al suelo.

## 6. Puertas (la puerta primero, ROJA; el modelo; VERDE; romperla)

| puerta | qué asevera | mutación que la pone roja |
|---|---|---|
| `guarda_aire()` (reescrita) | salida = rendija del alero + ondas; `potencia_disipada` = 9.22; ΔT ≤ 15; imprime el margen | tacos = 541 (tira continua) → 20.4 K; `rehundido_trasera` = 3 con `rehundido_chapa` = 1 → rendija 1.5 → 15.1 K a 9.22 W |
| **nueva** `guarda_rebaje_chapa()` | `rebaje_chapa` ≥ 2 t; `rehundido_chapa` ≥ 1 (un reborde más fino no se fresa); suelo = `rehundido_acrilico`; en el tramo trasero, suelo = pared del bolsillo (u = `rehundido_trasera`) y ninguna pared < `pared_rebaje_trasera`; labio del bolsillo ≥ 3 de hondo; `radio_borde` = `radio_chapa` + `rehundido_chapa`; cajeado de brida = `rebaje_chapa`; retiro del marco = `rehundido_chapa` + t + `hol_piel`; las tres chapas entran `rebaje_chapa` − `hol_piel` por lado | `rehundido_chapa` 0.5; `rebaje_chapa` 2; `cara_anillo_trasera` 20 (pared 2); `rehundido_trasera` 3.5 (aleta de 0.5) |
| `guarda_trasera_capturada()` | `aire_labios` = 2.5 con la chapa rehundida (u0 = 4); el labio del bolsillo de 3 retiene; chaflán de la plancha recalculado | `rehundido_trasera` 3 → aire 1.5 < junta |
| `guarda_miembro_alto()` | como hoy (200 N sola, 111 MPa, bridas) con la brida en su cajeado y las roscas desde z = 11 | igual que hoy |
| `guarda_marco()` | la pata trasera con 1 menos | — (decide 28 o 29) |
| `canario_techo()` | cada mutación de arriba salta por SU aserto (texto), como `canario_trasera()` | — |
| `check_dxf.techo_macizo()` (nueva) | `miembro_alto_2d.dxf`: ningún contorno cerrado dentro del blank salvo los cuatro M4 de las bridas | un DXF con una ranura |
| `check_dxf.anillo_tiene_rebaje_chapa()` (nueva) | en el DXF de la cara del anillo: el rebaje de 1..3 por el contorno de las chapas, fundido con el bolsillo de la trasera en el tramo trasero, y los dos cajeados de brida; radios de 5.5 en `costilla_2d` donde hay chapa | — |
| `check_dxf` sobres | los tres desarrollos 5.7 más anchos; `costilla_2d` con el tramo trasero a 21 | — |

Renders: las dos vistas de siempre y **los dos primeros planos de la esquina de
arriba-atrás** (tres cuartos y perfil, los del 30-08 en `build/`) pasan a ser
renders del repo, porque lo que se juzga aquí es una esquina.

## 7. Lo que cambia para el taller

- **Mecanizado (anillos):** una pasada más en la cara interior de cada anillo —
  el rebaje de 3 × 2 por el contorno de las chapas, fundido con el bolsillo de la
  trasera en el tramo trasero — y dos cajeados de brida de 3 × (27.3 × 14.8) por
  anillo; radios de 5.5 (no 4.5) en las esquinas con chapa; el tramo trasero a
  21 de franja. El PLIEGO del anillo cambia de revisión.
- **Chapa:** el techo **sin ranuras** (blank 593.70 × 71.85, era 588.00); talón
  546.02 × 39.73; nariz 5.7 más ancha. Nada nuevo que plegar; el gotero, si entra,
  es un dobladillo más en el techo (§8).
- **Acrílico:** la trasera igual (552.32 × 237.18), con el chaflán de abajo
  recalculado.
- **Juntas:** 16 tacos de EPDM de 2.5 × 15 (adhesivo), en vez de dos tiras.
- **RFQ:** al mecanizado, el rebaje y los cajeados (mismo herramental que los
  bolsillos); a la chapa, nada nuevo que preguntar.

## 8. Lo que este documento NO cierra

- **El gotero** del labio del techo (§3.5): con la primera pieza.
- **La rendija de abajo** como entrada: no se cuenta; si algún día hace falta
  el margen, es un término más en `guarda_aire()`.
- **Los 9.22 W** siguen siendo un número de spec, no medido; y los módulos siguen
  fuera de todo presupuesto térmico.
- **El costado a 6 en el tramo trasero** (franja 24) sigue siendo decisión de
  mirada de Samuel; aquí se toma 21 con el costado a 3, que es lo de hoy.
- **La banda alta de la trasera** (75 mm bajo el labio a más de 10 MPa, spec
  29-08 §9): igual. La rendija no la toca.
- **La banda del valle, los paneles y la fila 1U**: tanda B, su spec.

## 9. Enmiendas que manda

| papel | qué |
|---|---|
| `2026-08-15-case-design.md` | rev. 27 en el historial; §5: techo macizo, chapas empotradas 1 en rebaje de 3, salida por el alero, 9.22 W |
| `2026-08-29-trasera-capturada-talon-nariz-design.md` | §3.5 y §9: la junta es a tacos y la rendija es la salida; §3.1: el bolsillo de la trasera a u = 4..15 con labio de 3 de hondo; §5: el techo B sin ranuras; §7: `guarda_aire` |
| `2026-08-29-marco-ventana-banda-estructural-design.md` | §3.2: el retiro bajo las chapas 1.65 → 2.65; la pata trasera; §4: `guarda_aire` ya no lee ranuras del DXF (nunca lo hizo) |
| `2026-08-27-case-esqueleto-visible-design.md` | «Lo que NO se toca: la ventilación» — superado: la salida cambió el 28-08 y aquí otra vez, con su puerta |
| `2026-08-28-costilla-pletina-design.md` | §4: el anillo lleva el rebaje de chapa y los cajeados de brida; radios 5.5 |
| `case/README.md` | piezas y BOM (techo sin ranuras, blanks +6, tacos), térmico (9.22 W, 10.4/13.3 K, entrada 46 ranuras/7 193 mm² — hoy dice 44 y 6 781), orden de montaje |
| `case/PLIEGO.md` | rev. 27: anillo (rebaje, cajeados, radios, franja trasera 21), techo macizo, desarrollos, juntas |
| `case/RFQ.md` | rev. 26: al mecanizado el rebaje y los cajeados; a la chapa el techo sin ranuras |
