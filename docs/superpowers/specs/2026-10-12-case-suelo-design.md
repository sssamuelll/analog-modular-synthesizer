# El suelo: el case sin tabla

**Fecha**: 2026-10-12 · **Estado**: **firmado el 12-10** (versión 2, después de la junta) en el acta 4 (https://claude.ai/artifact/7PvsQ3aUfGtEdt7jj936kV):
- D-T1: **patas de 10, las de hoy**;
- D-T2: **los tornillos del suelo, desde abajo**;
- el papel: «Arma el plan».

**Sucede a**: la D-S4 del papel de la persiana (`2026-10-11-case-persiana-design.md` §8), firmada «quitar» el 11-10 a las 23:00 (ficha `quitar_tabla` del acta 3) ·
**Base**: `main` en `38d2ac4` (12-10): la persiana (#412), sus deudas (#419) y el aire con el plano neutro y la potencia de la v5 (#421) ·
**Se apoya en**:
- `2026-09-05-fuente-v5-ladrillo-design.md`: D-V1, la fuente afuera; §6.3, el suelo abierto; §7, *«No se reabre la cascada»*;
- `2026-09-03-fuente-v4-liston-design.md` §8, que le exige al case *«las dos placas dentro del mismo recinto de acero, porque R lleva 230 V y C lleva los tres tabs contra la pared»*;
- `2026-08-30-techo-macizo-chapas-empotradas`, por la nariz y el talón con su pie sobre la tabla;
- `2026-08-28-costilla-pletina`, por el anillo y sus tres M5 del canto inferior ·

**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, la persiana, el techo, la trasera y su rejilla baja, ni **el chasis de la fuente** (§4) ·
**Cifras**: las del aire salen de `case/cad/suelo.py`. Es propuesta, no puerta, igual que `persiana.py`, y sin el suelo reproduce `_tiro()` exacto (`autocomprobacion()`). Las de la chapa (flecha, amarre, tornillos e insertos) son de Elke Brandt, con su fuente al lado de cada una ·
**Junta** (12-10):
- el censo de impacto de Amina Halcyon: 212 entradas en 29 ficheros;
- Adrian Serrano: 1 BLOCKER, 5 HIGH;
- Elke Brandt (fabricación, sujeción y montaje): 3 altas.

La versión 1 tenía tres errores de fondo:
- **sacaba el chasis**, que es el disipador de la cascada;
- **estimaba en un 10 % el roce del canal** bajo el suelo, y en ese camino se come hasta un tercio de la presión;
- **avellanaba los M4** de la nariz y del talón en un pie de 1,5, donde el cono no asienta.

Cada corrección dice de dónde salió.

---

## 0. En una línea

La tabla de nogal se va. En su sitio entra una chapa de aluminio negro de 3 mm, del tamaño justo de la huella del cuerpo, que hace los trabajos de la tabla: amarra los dos anillos por abajo y recibe la nariz, el talón, las patas y el chasis de la fuente. Además hace uno nuevo, que es ser la entrada de aire. El chasis no se mueve de donde está.

---

## 1. Lo que dijo Samuel

- 11-10, acta 3, nota a la ficha de la tabla: *«pero ojo, estoy pensando en quitar la tabla, creo que es algo que nos puede beneficiar, que opinas tu?»*
- 11-10 a las 23:00, ficha `quitar_tabla`: **«Quitarla (suelo nuevo)»**. La ficha decía lo que cuesta: *«hace falta un suelo nuevo, una chapa negra perforada sobre las patas que cierre por abajo (polvo, dedos) y deje entrar el aire. Y se va el único material cálido.»*
- 12-10, en conversación: *«yo ya te lo he dejado claro que la tabla se iba no?»*

Este papel no reabre esa firma. Dice cómo es el suelo nuevo.

---

## 2. Lo que hace hoy la tabla, y quién lo hace después

| trabajo | hoy | después |
|---|---|---|
| amarrar los dos anillos por abajo | 6 M5 a rosca ciega en el canto inferior de los anillos, 3 por anillo (x = 53,3 · 159,9 · 266,5). Por anillo, uno en agujero redondo y dos en ranura de 10,5 por la veta | **el suelo**, con los mismos 6 M5 en las mismas roscas, los seis en agujero redondo. En planta y en torsión amarra mejor que la tabla; de lado, peor (§3.5) |
| recibir la nariz y el talón | 3 + 3 M4 avellanados por sus pies, desde dentro | **el suelo**, con M4 de cabeza de botón a tuercas de presión (§3.4 y D-T2) |
| recibir las patas | 4 patas de goma Ø20 × 10, bajo las esquinas de los anillos | **el suelo**, en los mismos sitios |
| recibir el chasis de la fuente | 4 M4 a tuerca remachable en el suelo del chasis, desde debajo | **el suelo**, igual (§4) |
| cerrar por abajo | 30 mm de nogal macizo | **el suelo**. Por sus agujeros de 5 no pasan dedos ni tornillos sueltos; el polvo sí (§6) |
| ser la base que se ve | losa de nogal de 30, canto R8, que vuela 40 por los cuatro lados | **se va**. Queda una línea de sombra alrededor (§3.3) |
| ser el asa y el parachoques | volaba 34 mm más allá de la persiana | **el canto del suelo**, metido 6 mm y con R0,5 (§3.3) |
| sujetar los cables | bridas atornilladas a la madera | **el suelo**: las bridas pasan por los agujeros del campo, desbarbados |
| recibir la pieza de la entrada (#130) | el README la manda a la tabla; el budget, al pie del talón; el `.scad`, a un larguero que ya no existe | **queda para el relevo de la v5** (§8, H1). Si va al suelo, son dos insertos más |
| — | — | **respirar**: el aire entra por abajo (§5) |

---

## 3. El suelo

### 3.1 Qué es

Una chapa de 6082-T6 de **3 mm**, anodizada en negro, que es la aleación y el acabado de todo el cuerpo (papel de la persiana §7.1). Mide **568,62 × 307,76**:

- de ancho, de cara de fuera a cara de fuera de los anillos;
- de largo, el canto inferior del anillo de chaflán a chaflán (los 319,76 de fondo menos los dos chaflanes de 6).

Va debajo de los anillos, de y = −3 a 0.

**El plano del suelo interior no se mueve.** Está en y = 0 desde el 27-08 (`guarda_piso()`), y nada de lo que hay encima cambia de sitio. El aparato pierde 27 mm de alto: los 30 de nogal menos los 3 de chapa. `ancho_exterior` sigue sin lector, porque el suelo va a ras de los anillos, no de las persianas.

### 3.2 Por qué 3 mm

Lo decide la mano, no el peso. El suelo carga con él mismo, con la trasera apoyada en el pie del talón y con el chasis, que va en sus cuatro M4. Con eso cede 0,31 mm, y 0,41 si con lo de dentro el chasis llega a 4 kg. Son cifras del modelo de Elke, con el chasis en sus tornillos y el campo en L.

Con una mano de 200 N (`carga_mano`) en el centro, Elke modeló la chapa como una parrilla de vigas, con nariz y talón como vigas de borde. Comprobó el modelo contra Timoshenko y se separa menos del 1 %:

| | 3 mm | 2 mm |
|---|---|---|
| flecha con la mano | 2,3–3,8 mm | 5,5–10,2 mm |
| tensión en el puente del campo | 53 MPa | 120 MPa |

**Con 2 mm**, la mano empuja la chapa hasta la mesa, y en el borde de los agujeros, que concentra la tensión de 2 a 3 veces, el aluminio se deforma para siempre. **Con 3 mm no pasa ninguna de las dos cosas.**

El criterio nuevo sustituye al aserto 2 de `guarda_piso()`, que medía la tabla con 200 N en medio del vano contra 0,60 mm. Con `carga_mano` en el centro, la chapa no plastifica en el puente del campo y no toca la mesa.

### 3.3 Lo que se ve

- **De frente:** debajo del chaflán de la nariz, el canto negro de 3 mm metido 6 mm, y debajo las patas.
- **De lado:** bajo la persiana, cuyo canto queda 0,3 sobre y = 0, el canto del suelo 6 mm por detrás de su cara.

Queda una línea de sombra por los cuatro lados. El cuerpo flota sobre la mesa la altura de las patas más los 3 de chapa (D-T1). Es la piedra negra sobre cuatro patas del acta 3.

**El aparato se levanta con los dedos bajo ese canto**, que deja de ser el vuelo de 34 mm de la tabla. Por eso el canto de abajo lleva un redondeo de **R0,5**, no un chaflán de 0,2.

Se va el único material cálido del case. La ficha que firmó Samuel ya lo decía.

### 3.4 Cómo se sujeta

- **Los anillos.**
  - Van con 6 M5 × 12 ISO 7380 de cabeza de botón, desde abajo. Entran 9 mm de rosca en los 10 útiles del anillo (PLIEGO §6.1); un M5 × 16 tocaría fondo y no amarraría nada.
  - Los agujeros son **redondos de Ø6**: aluminio contra aluminio se dilata igual, así que las ranuras de la veta sobran y `holgura_veta` se retira. El medio milímetro de juego absorbe la posición entre dos anillos mecanizados por separado.
  - El agujero queda a 7,0 del canto, contra los 8,25 que pide la regla del repo (1,5 veces el diámetro, `params.scad` l.391-395). Se declara como excepción: arrancar ese borde pide del orden de 4 kN.
  - Un M5 avellanado no cabe: la cabeza ISO 10642 M5 mide 3,1 de alto.
- **La nariz y el talón.** Los tornillos entran **desde abajo** (D-T2, firmada):
  - M4 × 8 ISO 7380 de botón, por agujeros de paso en el suelo, a tuercas de presión CLS-M4 prensadas en los pies de la nariz y del talón (chapa de 1,5).
  - Las cabezas quedan bajo el suelo, dentro de los 10 mm de las patas, y los doce tornillos del suelo se alcanzan desde fuera.
  - **No avellanados.** En un pie de 1,5 el avellanado de la cabeza ISO 10642 (2,48 de alto) atraviesa la chapa y deja el cono 0,98 mm por debajo. Con la tabla se clavaba en el nogal y nadie lo vio.
  - El M4 queda a 6,75 del canto libre del pie, y la tuerca pide unos 6,9 (Elke, de memoria). **Los dos pies crecen medio milímetro**: la nariz de 20,5 a 21 y el talón de 22,5 a 23. Siguen difiriendo en 2, que es lo que pide `guarda_talon()`. La hoja de PEM lo confirma (H4).
  - Por dentro, sobre cada pie, asoma el cuerpo de la tuerca, no la cabeza. `guarda_talon()` pasa a medir la tuerca contra la trasera.
- **Las patas.** Van en espárragos de presión de cabeza plana FH-M4, a ras de la cara de arriba, bajo el canto del anillo.
  - El largo del espárrago tiene que casar con la profundidad del casquillo de la pata (H3). Si es más largo, la pata no asienta y el aparato carga en la punta.
  - Si se quiere no depender de que la cabeza quede a ras, el anillo lleva un rebaje de Ø9 × 0,3 sobre cada espárrago, en la misma puesta que sus M5.
- **El chasis.** Lleva sus 4 M4 desde abajo a sus tuercas remachables, como hoy, por agujeros de paso en el suelo.
- **Los insertos.**
  - Van de la serie de acero o de inoxidable (CLS, FH, SO o CLSS, FHS, SOS), **nunca de la de aluminio**: esa pide chapa de dureza HB 89 o menos, y el 6082-T6 ronda HB 95.
  - Con 3 mm sobra chapa, y sus distancias al borde pasan en todos los sitios (H4).
  - Se prensan **después** de anodizar: el baño ataca el cincado, deja ácido atrapado en el inoxidable, y los anodizadores no aceptan piezas con insertos.
  - Sus agujeros se cortan a cota nominal +0,03/+0,05, porque el anodizado los cierra unos 0,02.
  - El orden del taller es láser, desbarbado, anodizado y prensa.
- **La masa eléctrica.** Es uno de los seis M5 por anillo, no un séptimo: si fuera un séptimo, los tacos de la persiana, que cuelgan de esos M5 (`persiana.py`, `cb._m5_tabla_x()`), se moverían.
  - En el suelo y en el canto del anillo lleva un círculo de **Ø12 sin anodizar** alrededor de ese M5, y una arandela dentada bajo la cabeza.
  - Se prueba con **≤ 0,1 Ω a cuatro hilos**, como el criterio 3 del cupón (PLIEGO §6.1).
  - Hoy solo se enmascara el punto de la cara interior del anillo, que no toca el suelo.
  - **Este papel no promete blindaje**: la trasera es de PMMA, la persiana es una reja, y las juntas van anodizadas. Si con el cordón de dos hilos de la v5 hace falta esta masa lo decide el relevo de la v5 (§8, H1).

### 3.5 Lo que amarra

Las cifras son de Elke:

- **En planta y en torsión, mejor que la tabla.**
  - A cortante, la chapa da 78 000 N/mm y la tabla de nogal unos 21 000 (G ≈ 700 MPa, estimado).
  - Hoy cada anillo cuelga de un solo perno redondo, porque sus dos ranuras corren justo en esa dirección. Con la chapa son tres.
- **De lado, peor.** La tabla de 30 empotraba el canto del anillo, y la chapa de 3 trabaja como una bisagra.
  - El giro que el suelo le frena a cada anillo baja a unos 580 N·m/rad, desde 3 200–5 900 con la tabla.
  - Si el suelo fuera lo único que frena, 200 N de lado en lo alto moverían el remate unos 11 mm, cuando con la tabla eran 1–2.
  - No es lo único: también frenan la trasera, que se acuña en sus bolsillos; las bridas del techo; y, con el aparato lleno, los paneles.
  - El repo ya deja el descuadre (#203) para el prototipo. **Se prueba con el suelo de chapa y sin paneles**, que es el peor caso (§8, H5).

### 3.6 El montaje

Es el mismo de hoy, cambiando la tabla por el suelo:

1. En el banco, el suelo con la nariz y el talón.
2. El suelo se pone de canto sobre el tramo de abajo del anillo A.
3. Entra el anillo B, con el suelo todavía vacío, que es lo que deja llegar a los doce M4 del marco B.
4. El chasis entra al final por el frente, y sus cuatro M4 se aprietan desde debajo del suelo.

**Para el servicio** (D-T2): se voltea el aparato, se sueltan los doce tornillos del suelo y los cuatro del chasis no hace falta tocarlos. El suelo baja entero, con el chasis encima, sin tocar ningún anillo ni ningún panel. Antes se desenchufan los cables del chasis. Cuánto cable hace falta para llegar a los conectores lo dice el relevo de la v5 (H1).

---

## 4. El chasis se queda

**La versión 1 lo sacaba, y estaba mal.** Daba por muerta la caja de acero porque la v5 sacó la etapa de red. Pero la caja tiene otros dos trabajos (`params.scad` l.1842-1846), y nadie los hereda:

1. **Es el disipador de la cascada.** Los tres TO-220 (`U1`, `U2`, `U3`) atornillan sus tabs a su pared, y con eso la Tj de `U2` baja de 101 a unos 61 °C.
   - La v5 sacó la placa R (la de red), pero no la C (la cascada): su §7 dice *«No se reabre la cascada. U1/U2, los LT3045/LT3094 y U3 se quedan donde están»*.
   - La v4 §8, que la v5 no reabre, le exige al case la caja de acero para que C apoye *«los tres tabs contra la pared»*.
   - El papel del recinto partido (#316) proponía la cascada fuera de la caja, pero está **sin firmar**. Su propio §6.1 dice que el disipador en placa *«no da»* con el modelo de la v4, y su §6.3 deja abierto el acoplo de una placa sin apantallar junto a los conmutadores.
2. **Es la referencia de tierra**, el espárrago único de PE.

Además, del bloque del chasis en `params.scad` cuelgan cosas que no son del chasis:

- `k_factor`, que da los desarrollos de la nariz, del talón y del techo;
- siete cotas que lee `hardware/01-power-supply/v3/kicad/build_pcb.py`, con un `assert` al importarse, del que dependen tres puertas del pre-push.

**Así que el chasis se queda como está y se atornilla al suelo** en lugar de a la tabla. Para el suelo eso supone dos cosas:

- La caja tapa x 112–288, z 206–545. Ahí no van agujeros, y el campo se hace en L (§5).
- Pesa unos 2,4 kg de chapa más lo de dentro, cerca del anillo derecho: es una carga pequeña (§3.2).

**Lo que queda para otro papel**, el relevo de la v5 en el case:

- encoger la caja a la placa C (menos de 200 × 100 sin R);
- lo que dejó el toroide que se retiró (su refuerzo y sus 97 mm de holgura);
- el PE frente a la M2 de la v5;
- el conector del cordón.

Elke propone otra casa para los TO-220: el propio suelo, que es aluminio de 3 mm en el aire más frío del case, con lámina aislante y tres FHS-M3 en una zona sin agujeros. Eso también es del relevo.

---

## 5. El aire

**El suelo es un camino en serie, no un hueco suelto.** El aire entra por la rendija que dejan las patas en el perímetro, corre por el canal de `alto_pie` entre la chapa y la mesa, y sube por el campo de agujeros:

    dp = ρ/2 · (Q / (C_D · A_rendija))² + 12 μ L Q / (W h³) + ρ/2 · (Q / (C_D · A_suelo))²

La rendija y los agujeros son orificios, cuya pérdida va con Q². El canal es laminar (Poiseuille entre placas), y su pérdida va con Q. Con un término lineal la chimenea deja de ser P = k ΔT^1,5, así que `suelo.py` la resuelve con dos bisecciones:

- el plano neutro, por balance de masa;
- el salto, por balance de energía.

**Lo que corrigió la junta:**

- **El roce del canal.** Va con h³. La versión 1 lo daba como «del orden del 10 % del tiro», y Serrano lo estimó del orden de toda la presión del camino. Con el modelo:
  - a patas de 10, le quita al suelo entre el 12 y el 22 % de lo que bajaría el salto sin roce (0,4–0,7 K de 3,3);
  - a patas de 20, entre el 2 y el 4 %.
- **La rendija.** Es el perímetro del suelo (1 752,75, no el del cuerpo, 1 777) menos las cuatro patas: 1 673 mm. Con un costado tapado, la pared tapa también su rendija: 1 405.
- **El campo no puede ir debajo del chasis.** Se hace en L:

| zona | x | z | área |
|---|---|---|---|
| A, a la izquierda del chasis | 45–273 | 24–196 | 39 179 mm² |
| B, delante del chasis | 45–102 | 196–545 | 19 750 mm² |

  Con Ø5 al tresbolillo cada 8 (el patrón Rv 5-8, un 35,4 % abierto) el campo abre hasta 20 876 mm², y se usan 20 000. Casi todo el perímetro queda a 25–30 mm de un agujero. El tramo de atrás a la derecha queda a unos 200, por debajo del chasis. Por eso el largo del canal se da como **60 mm** (estimado) y **120 mm** (el pesimista).

Las cifras, con 64,22 W, las dos persianas y 20 000 mm² abiertos (`python case/cad/suelo.py`):

| | salto | pesimista | un costado tapado (pesimista) | sala a 45 °C (pesimista) |
|---|---|---|---|---|
| hoy, con la tabla | 16,88 K | 18,86 K | 26,04 K ✗ | 20,47 K ✗ |
| patas de 10, canal de 60 | 14,33 | 15,92 | 21,01 ✗ | 17,28 |
| patas de 10, canal de 120 | 14,67 | 16,26 | 21,50 ✗ | 17,64 |
| patas de 20, canal de 60 | 13,31 | 14,86 | 19,39 | 16,13 |
| patas de 20, canal de 120 | 13,40 | 14,94 | 19,50 | 16,21 |

El techo es de 20 K. La tabla dice cuatro cosas:

- **El suelo funciona con las dos patas.** El pesimista baja de 18,86 a unos 16 con las de 10 y a unos 14,9 con las de 20.
- **El HUECO de la sala se cierra con las dos.** A 45 °C, el pesimista queda entre 16,1 y 17,6.
- **Con un costado tapado, solo pasan las de 20**, con 19,4–19,5 K, y sin mucho margen. Con las de 10 sigue la condición de uso del pliego (D-S11).
- **Con las de 20 el canal deja de importar**: doblar su largo mueve 0,1 K. Con las de 10 mueve 0,3–0,5, y es lo que menos se sabe del modelo (H2).

**La rendija de las patas pasa a ser parte del aire.** El aparato necesita una superficie dura con la altura de las patas libre debajo. Va al PLIEGO §7 como condición de uso, igual que los costados: sobre una alfombrilla o un paño vuelve al caso «hoy». Y el comentario de `params.scad` que dice que `alto_pie` no entra en ninguna derivación (l.1376-1378) deja de ser verdad.

**Lo que cambia en la puerta del aire:**

- El HUECO de los costados lo juzga hoy `guarda_aire()` con C_D 0,65. Con el suelo, el nominal pasaría y el pesimista fallaría, y el HUECO dejaría de publicarse en silencio. **Pasa a juzgarse con el pesimista**, como ya se juzga el de la sala.
- Los márgenes de `canario_techo()` se calibraron sin suelo: el plan comprueba que siguen mordiendo.

**Lo que la cuenta no ve:**

- **El flujo de debajo es 2D y converge.** El canal de un solo largo es la parte más cruda del modelo (H2).
- **El C_D de agujeros cortos** (3 de espesor por 5 de diámetro). Se supone el mismo `CD_TIRO` que el resto.
- **La rejilla baja de la trasera se queda**: sin ella el pesimista sube unos 0,9 K.

---

## 6. Lo demás

- **Líquidos.** Lo que entra se va por el suelo; la tabla lo retenía dentro. La cascada sigue en su caja con tapa. El ensayo de derrame (D-S10 de la persiana) añade un criterio: el agua que entra sale por el suelo y no se encharca en él.
- **Polvo.** El suelo es una entrada de aire, y aspira el polvo de la mesa. Por dentro se aspira quitando la persiana, y el suelo, por debajo.
- **Dedos.** Por un agujero de 5 no entra un dedo, ni un tornillo de los que se caen.
- **Peso.** Salen los 5,06 kg de nogal y entran 1,25 de chapa: −3,8 kg.
- **Taller.** Se va el carpintero. El suelo va al mismo taller de chapa que la nariz, el talón y el techo, con cuatro cláusulas en el pliego:
  - los agujeros se cortan salteados, para repartir el calor;
  - planitud de **≤ 1 mm** en la chapa suelta, medida antes de anodizar; si hay que nivelar, se nivela antes, nunca después;
  - desbarbado a máquina por las dos caras, con la arista de arriba matada, porque por ahí pasan bridas;
  - el anodizado y, después, la prensa de insertos.

  La chapa perforada de catálogo (Rv 5-8, DIN 24041) no compensa para esta tirada:
  - viene en otras aleaciones, que anodizan con otro tono;
  - el campo sale rectangular;
  - el contorno se corta después, con ±0,5–1 de error contra el campo.
- **Las patas**, con un criterio de compra nuevo. El de hoy, flecha ≥ 0,25 mm con 22,8 N, era para aislar los 100 Hz de un toroide que ya no está. Ahora se quiere una pata firme:
  - altura nominal ± 0,2 mm, porque es parte de la entrada de aire, y cuatro patas desiguales cojean;
  - ≤ 0,3 mm con 50 N, o sea goma de Shore 60–70 A, no de 45–55;
  - un compuesto que no manche el barniz;
  - la profundidad del casquillo y su par en la hoja.

  `guarda_paticas()` cambia de criterio, no se borra.

---

## 7. Lo que cambia en el repo

El censo de la junta tiene 212 entradas. Por fichero:

- **`params.scad`**:
  - `t_base` (30) pasa a `t_suelo` (3);
  - se retiran `r_canto_tabla`, `E_madera`, `vuelo_zocalo` y `holgura_veta`;
  - `flecha_pie` cambia por el criterio nuevo de la pata;
  - **el bloque del chasis se queda entero.**
- **`sam17_case.scad`**:
  - `bandeja_base()` y `bandeja_base_2d()` pasan a ser el suelo, sin vuelo. La cadena de coordenadas locales de la tabla («x local = vuelo + z») está copiada en el `.scad`, en `check_dxf.py` y en el budget, y hay que cambiarla en todos los sitios a la vez;
  - se retira `canto_redondeado()`;
  - `paticas()` baja a y = −`t_suelo` y sale de `assembly_madera()`, que hoy es el único camino por el que las patas llegan a Blender;
  - `lienzo_2d()`, declarado de acrílico, deja de llevar el suelo;
  - la razón de que `n_agujeros()` exista aparte (la ranura) desaparece.
- **`clearance_budget.py`**:
  - el aserto 2 de `guarda_piso()` pasa al criterio del §3.2;
  - `guarda_paticas()` cambia de criterio;
  - se retira `canario_persiana_tabla()`: el suelo ya no pasa bajo la persiana, y las dos cajas no se cruzan nunca;
  - el suelo entra en el aire como camino en serie;
  - el HUECO de los costados se juzga con el pesimista;
  - se repasan los márgenes de `canario_techo()`;
  - `_envolvente_m2()` deja de restar el suelo como apoyado en la mesa.
- **`check_dxf.py`**: `guarda_zocalo()`, que vive aquí, pasa a ser la puerta del suelo:
  - el censo de taladros: 6 M5, 6 M4 de nariz y talón, 4 FH y 4 M4 del chasis;
  - y el campo de agujeros, que no pisa el canto del anillo, los pies, las patas ni la huella del chasis, guarda la distancia de PEM a cada inserto y cumple un puente de 1 vez el espesor. El 0,8 del repo es la regla del PMMA.

  El DXF lleva unos 1 000 agujeros: hay que medir los tiempos de `check_dxf` y del `TIMEOUT_S` de `gates.py`.
- **Renders y piezas**: `render.py` entrega `mad`, que `render_persiana.py` y `piezas.py` borran por nombre. También cambian `render_bahia.py`, `plano_chasis.py`, `piezas.scad` y `export.ps1`.
- **Papeles**:
  - el PLIEGO: sale la TABLA y entra el SUELO, con las cuatro cláusulas del §6; el §6.1 del anillo gana el círculo de Ø12 del canto; el §7 gana la condición del apoyo; y las patas cambian de criterio;
  - el RFQ (§B);
  - el README (BOM, montaje y estado);
  - la spec maestra (§4, §5, §9, §10 y §11);
  - el §12 del papel de la persiana, que todavía dice «en espera» de la D-S4.

---

## 8. HUECOS

1. **H1 — El relevo de la v5 en el case**:
   - la caja encogida a la placa C, o la cascada sobre el suelo;
   - el PE frente a la M2;
   - el conector del cordón y la pieza que recibe su tirón.

   No son de este papel. El suelo no le quita sitio a ninguno.
2. **H2 — El canal bajo el suelo.** Se mide el salto en la primera unidad, con las patas de la firma.
3. **H3 — La pata.** Falta la hoja: profundidad del casquillo, curva de carga y deformación permanente.
4. **H4 — Las hojas de PEM** (CLS, FH, SO). Las distancias al borde, los agujeros y la chapa mínima que da Elke son de memoria. Se piden a Samuel.
5. **H5 — El descuadre (#203).** Se prueba con el suelo de chapa y sin paneles.

---

## 9. Lo que Samuel decide

**Firmado el 12-10** en el acta 4, sin notas:
- **D-T1: patas de 10**, las de hoy. Es la que recomendaba Elke; la mía eran las de 20.
- **D-T2: desde abajo.**
- **El papel: «Arma el plan».**

Con patas de 10 sigue la condición de los costados libres (D-S11), porque con uno tapado el pesimista da 21,0–21,5 K. También sigue el HUECO de los costados, que la puerta pasa a juzgar con el pesimista. El canal pesa 0,3–0,5 K y se mide (H2).

Las fichas, como se presentaron:

| | qué | recomendé | lo otro, y lo que cuesta |
|---|---|---|---|
| **D-T1** | las patas | **de 20**. Con un costado tapado pasa (19,4–19,5 K), así que el aparato puede ir pegado a otro equipo por un lado. El canal deja de importar, y el cuerpo flota 23 mm | **de 10**, las de hoy. Flota 13 mm, y la pata es el doble de firme de lado (0,16 contra 0,32 mm al meter un jack, las dos imperceptibles). Con un costado tapado no pasa (21–21,5 K). **Elke recomienda estas**: con el suelo libre por los dos costados, los 0,7 K de más no hacen falta |
| **D-T2** | por dónde entran los M4 de nariz y talón | **desde abajo**, a tuercas en sus pies. Los doce tornillos del suelo se alcanzan desde fuera, y el suelo sale por abajo con el chasis sin tocar ningún anillo | **desde dentro**, como hoy. Para sacar el suelo hay que abrir el case. Desde abajo cuesta seis tuercas en pies de 1,5, con el M4 a 6,75 del canto del pie contra unos 6,9 que pide la tuerca: el pie crece medio milímetro, y se confirma con la hoja (H4) |
| | el papel | — | — |

---

## 10. El orden

1. ~~Papel, versión 1~~ y ~~junta~~.
2. ~~Versión 2: este papel~~.
3. ~~Acta con renders y firma~~ (12-10).
4. Plan.
5. Tanda, con su PR y sus issues.
