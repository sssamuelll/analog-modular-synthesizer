# El suelo: el case sin tabla

**Fecha**: 2026-10-12 · **Estado**: versión 1, para la junta ·
**Sucede a**: la D-S4 del papel de la persiana (`2026-10-11-case-persiana-design.md` §8), firmada «quitar» el 11-10 a las 23:00 (ficha `quitar_tabla` del acta 3) ·
**Base**: `main` en `38d2ac4` (12-10): la persiana (#412), sus deudas (#419) y el aire con el plano neutro y la potencia de la v5 (#421) ·
**Se apoya en**: `2026-09-05-fuente-v5-ladrillo-design.md` (D-V1, la fuente afuera; §6.3, el suelo abierto; §6, «queda la cascada, que es una placa, no un cajón»), el PR #316 (la cascada fuera de un cajón de acero), `2026-08-30-techo-macizo-chapas-empotradas` (nariz y talón con su pie sobre la tabla) y `2026-08-28-costilla-pletina` (el anillo y sus tres M5 del canto inferior) ·
**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, la persiana, el techo, la trasera y su rejilla baja (§5) ·
**Cifras**: el aire sale de `clearance_budget._huecos()` y `_plano_neutro()` con un hueco más en y = 0 (la receta está en §5); los pesos, de las cotas de `params.scad`.

---

## 0. En una línea

La tabla de nogal se va, y en su sitio entra una chapa de aluminio negro de 3 mm, del tamaño justo de la huella del cuerpo. Hace los trabajos de la tabla —amarra los dos anillos por abajo y recibe la nariz, el talón y las patas— y uno nuevo: es la entrada de aire. Con la tabla se va el chasis de acero de la fuente vieja, que vivía atornillado a ella y que la v5 ya había sacado del instrumento.

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
| amarrar los dos anillos por abajo | 6 M5 a rosca ciega en el canto inferior de los anillos, 3 por anillo (x = 53,3 · 159,9 · 266,5): uno redondo y dos en ranura de 10,5, por la veta | **el suelo**, con los mismos 6 M5 en las mismas roscas, los seis en agujero redondo (§3.4) |
| recibir la nariz y el talón | 3 + 3 M4 avellanados por sus pies, desde dentro | **el suelo**, con los mismos tornillos a tuercas de presión en la chapa |
| recibir las patas | 4 patas de goma Ø20 × 10, bajo las esquinas de los anillos | **el suelo**, en los mismos sitios |
| cargar el chasis de la fuente | 4 M4 a tuerca remachable, desde debajo | **nadie**: el chasis se va (§4) |
| cerrar por abajo (polvo, dedos) | 30 mm de nogal macizo | **el suelo**, con agujeros de 5 (§3.2) |
| ser la base que se ve | losa de nogal de 30, canto R8, que vuela 40 por los cuatro lados | **se va**. Queda una línea de sombra alrededor (§3.3) |
| — | — | **respirar**: el aire entra por abajo (§5) |

---

## 3. El suelo

### 3.1 Qué es

Una chapa de 6082-T6 de **3 mm**, anodizada en negro: la aleación y el acabado de todo el cuerpo (papel de la persiana §7.1). Mide **568,62 × 307,76**: de cara de fuera a cara de fuera de los anillos, y a lo largo del canto inferior del anillo, de chaflán a chaflán (los 319,76 de fondo menos los dos chaflanes de 6). Va debajo de los anillos, de y = −3 a 0.

**El plano del suelo interior no se mueve.** Está en y = 0 desde el 27-08 (`guarda_piso()`), así que nada de lo que hay encima cambia de sitio. El aparato pierde 27 mm de alto: los 30 de nogal menos los 3 de chapa. `ancho_exterior` sigue sin lector: el suelo va a ras de los anillos, no de las persianas.

### 3.2 Por qué 3 mm y agujeros de 5

- **Carga poco.** El peso del case va de anillo a pata con el suelo en medio, apretado entre los dos. Lo que cuelga del suelo es él mismo (1,25 kg) y la placa de la cascada (§4).
- **Los tornillos van por debajo**, con las cabezas escondidas en los 10 mm de las patas. En 3 mm cabe el avellanado de un M4. El M5 avellanado no cabe: su cabeza ISO 10642 mide 2,8 de alto y deja 0,2 mm de chapa, que no aguanta. Los M5 van con cabeza de botón, que tampoco se ve. Lo confirma la junta.
- **Los agujeros**: Ø5 al tresbolillo cada 8 mm, un 35 % abierto. El puente entre agujeros mide 3, y la regla del repo pide 2,4 (0,8 veces el espesor). Para los 20 000 mm² abiertos del §5 hacen falta unos 57 000 mm² de campo. Va centrado entre los dos anillos y lejos de los pies de la nariz y del talón, de las patas y de la placa de la cascada: entre x ≈ 35 y 285 y entre z ≈ 24 y 544 caben 130 000.
- **Por qué no líneas como la persiana.** El suelo solo se ve con el aparato levantado. Un campo de agujeros redondos es lo más barato de cortar, y cualquier taller de chapa lo hace bien.

### 3.3 Lo que se ve

- **De frente**: debajo del chaflán de la nariz, el canto negro de 3 mm, metido 6 mm, y debajo las patas.
- **De lado**: bajo la persiana, cuyo canto queda 0,3 sobre y = 0, el canto del suelo, 6 mm por detrás de su cara.

Queda una línea de sombra por los cuatro lados, y el cuerpo flota 13 mm sobre la mesa: 10 de patas y 3 de chapa. Es la piedra negra sobre cuatro patas del acta 3 (`sin_tabla_c12.jpg`, `sin_tabla_lado.jpg`).

Se va el único material cálido del case. La ficha que firmó Samuel lo decía.

### 3.4 Cómo se sujeta

- **Los anillos**: 3 M5 por anillo, desde debajo, a las roscas ciegas de hoy. **Los seis van en agujero redondo.** Las ranuras eran para que la madera se moviera con la estación; aluminio contra aluminio se dilata igual. `holgura_veta` se retira.
- **La nariz y el talón**: los 3 + 3 M4 avellanados de hoy, desde dentro, por sus pies. Roscan en tuercas de presión (PEM) en la chapa, por debajo.
- **Las patas**: las mismas cuatro, en los mismos sitios. Se roscan en espárragos de presión de cabeza plana (PEM FH-M4), cuya cabeza queda a ras de la cara de arriba, bajo el canto del anillo, sin levantarlo. La pata ya trae casquillo roscado moldeado.
- **La placa de la cascada**: cuatro separadores de presión en la chapa (§4).
- **La masa eléctrica**: un M5 por anillo, con el anodizado enmascarado en las dos caras, como el punto de unión que ya lleva el anillo. Sin eso, el suelo anodizado queda aislado del resto de la caja.

### 3.5 El montaje

Es el mismo de hoy, cambiando la tabla por el suelo:

1. En el banco se prepara el suelo con la nariz y el talón.
2. El suelo se pone de canto sobre el tramo de abajo del anillo A.
3. Entra el anillo B.

El paso «el chasis entra al final por el frente» desaparece. La placa de la cascada se atornilla al suelo antes de cerrar con el anillo B. El orden fino lo escribe el plan.

---

## 4. El chasis viejo se va

El modelo del case todavía dibuja, atornillado a la tabla, el chasis de acero de la fuente. Es una caja de 332 × 170 × 61 por dentro, de chapa de 1,5: unos 2,4 kg con su tapa y su refuerzo. Lleva:

- el refuerzo bajo el toroide;
- el espárrago de tierra;
- los tres TO-220 en la pared;
- la ranura de salida de cables;
- sus cuatro M4 a la tabla.

**Esa caja ya no existe.** La v5, firmada el 08-09, sacó del instrumento la etapa de red (D-V1). Su §6 dice que con ella se va *«el grueso del recinto de acero, que hoy ocupa el 30 % del suelo. Queda la cascada, que es una placa, no un cajón»*. El PR #316 ya había dejado escrito dónde vive lo que se queda: fuera de un cajón de acero, a la vista. Nadie quitó la caja del modelo, porque el relevo de la v5 quedó «pendiente de ejecutar». Sin tabla no tiene dónde atornillarse, y dimensionar el suelo para cargar una caja que ya no existe sería diseñar para un fantasma.

**En su sitio entra la placa de la cascada**, sobre cuatro separadores en el suelo, donde estaba el chasis y junto a la entrada del cordón. Se le reserva la huella que el chasis reservaba para su placa: 200 × 150. Su tamaño de verdad, su masa y el conector del cordón son del relevo de la v5, no de este papel (§8, H1).

**Con la caja se van:**

- `guarda_chasis()`;
- la regla de la pata como muelle contra los 100 Hz del toroide (`flecha_pie`, `F_TOROIDE`), porque dentro ya no hay toroide;
- las piezas y los DXF del chasis;
- sus filas del BOM y del pliego;
- su acero en los renders.

---

## 5. El aire

Las cifras salen del modelo del repo (`_huecos()`, `_plano_neutro()`), con los 64,22 W de la v5 y las dos persianas. El suelo entra como un hueco más a y = 0, en serie con la rendija que dejan las patas por todo el perímetro (1 777 mm por 10 de alto):

    a_suelo_ef = (a_suelo⁻² + a_rendija⁻²)^(−1/2),   a_rendija = 1 777 × 10

| abierto en el suelo | salto | pesimista | un costado tapado (pesimista) | sala a 45 °C (pesimista) |
|---|---|---|---|---|
| 0 (hoy, con tabla) | 16,88 K | 18,86 K | 26,04 K ✗ | 20,47 K ✗ |
| 10 000 mm² | 14,66 | 16,39 | 21,36 ✗ | 17,79 |
| **20 000 mm²** | **13,82** | **15,44** | **19,96** | **16,76** |
| 40 000 mm² | 13,4 | 14,9 | 19,3 | 16,2 |

El techo es de 20 K. La tabla dice cinco cosas:

- **20 000 es el codo.** De ahí en adelante manda la rendija de las patas: doblar el campo de agujeros gana 0,5 K.
- **El HUECO de la sala se cierra.** Con la sala de diseño a 45 °C, el pesimista pasa de 20,47 K, que falla, a 16,76.
- **El HUECO de los costados se queda, pero baja 6 K.** Con un costado contra una pared, el pesimista pasa de 26,04 a 19,96: pasa por 0,04 K, sin margen. La condición de uso del pliego sigue.
- **La chimenea aguanta más.** Al techo evacúa 111,9 W, o 94,7 en el pesimista; hoy son 82,9 y 70,1. Los 64,22 W son una cota de abajo (la enmienda M1 de la v5 aísla el +5 V digital), y el margen sobre ella pasa de 6 a 30 W en el pesimista.
- **La rejilla baja de la trasera se queda.** Con el suelo abierto y sin ella, el pesimista sube 0,9 K (16,3).

**Las patas**: con 20 000 abiertos, patas de 20 en vez de 10 bajan el pesimista de 15,44 a 14,74 K.

Hay dos cosas que la cuenta no ve, para la junta:

- **El canal de debajo.** Antes de subir por los agujeros, el aire corre hasta 160 mm por un hueco de 10 mm de alto. El flujo es laminar; a mano, la fricción se come del orden del 10 % del tiro. Está sin modelar.
- **El C_D de los agujeros.** Son agujeros cortos: 3 mm de espesor por 5 de diámetro. Se supone el mismo `CD_TIRO` que el resto.

---

## 6. Lo demás

- **Líquidos.** Lo que entra se va por el suelo; la tabla lo retenía dentro. Un charco en la mesa no llega, porque hay 10 mm de pata. El ensayo de derrame (D-S10 de la persiana) no cambia.
- **Polvo.** La entrada de abajo aspira el polvo de la mesa. Por dentro se aspira quitando la persiana, y el suelo se aspira por debajo.
- **Dedos.** Por un agujero de 5 no entra un dedo. Además, dentro ya no hay red: con la v5 solo hay continua de seguridad.
- **Blindaje.** La chapa cierra por abajo la caja de aluminio; el nogal no la cerraba.
- **Peso.** Salen los 5,06 kg de nogal y entran 1,25 de chapa: −3,8 kg. Con el chasis salen otros 2,4 kg de acero, más lo que llevaba dentro.
- **Taller.** Se va el carpintero. El suelo va al mismo taller de chapa que la nariz, el talón y el techo: corte láser y anodizado.

---

## 7. Lo que se retira

Es una lista de partida, y el censo de la junta la completa.

- **`params.scad`**:
  - `t_base` (30) pasa a `t_suelo` (3);
  - se retiran `r_canto_tabla`, `E_madera`, `vuelo_zocalo`, `holgura_veta` y el bloque del chasis;
  - el comentario de `suelo_persiana` («sobre la tabla») pasa a decir «sobre el plano del suelo», con el mismo valor.
- **`sam17_case.scad`**:
  - `bandeja_base()` y `bandeja_base_2d()` pasan a ser el suelo;
  - se retiran `canto_redondeado()` y todo `chasis*()`;
  - `paticas()` baja a y = −`t_suelo`.
- **`clearance_budget.py`**:
  - `guarda_zocalo()` pierde la veta y conserva el censo de taladros;
  - se retiran `guarda_chasis()` y la regla de la pata como muelle;
  - `guarda_piso()` deja de imprimir la flecha de la tabla;
  - el suelo entra en `_huecos()`.
- **`check_dxf.py`**: el DXF de la tabla pasa a ser el del suelo, con su campo de agujeros y su puerta: los agujeros no pisan tornillos, patas, pies ni canto de anillo, y cumplen el puente.
- **PLIEGO, RFQ y README**:
  - salen la fila de la TABLA y el carpintero, y las filas del chasis;
  - entra la fila del SUELO;
  - se reescribe el montaje.
- **Renders**: sale el nogal de la escena común.

---

## 8. HUECOS

1. **H1 — La placa de la cascada**: tamaño, masa, sitio y conector del cordón. Son del relevo de la v5. El suelo le reserva 200 × 150 y cuatro separadores.
2. **H2 — El canal bajo el suelo**: se mide al encender la primera unidad, con su salto.
3. **H3 — La pata**: sin el toroide ya no hay 100 Hz que aislar, pero cada pata carga unos 2,5 kg. El casquillo y la goma se piden con hoja de datos.

---

## 9. Lo que Samuel decide

| | qué | recomiendo | lo otro, y lo que cuesta |
|---|---|---|---|
| **D-T1** | el chasis viejo | sale en esta tanda | quedarse hasta el relevo de la v5: un suelo dimensionado para 2,4 kg de acero y su toroide, y agujeros tapados debajo de él |
| **D-T2** | las patas | las de hoy, de 10 | de 20: el pesimista baja 0,7 K y el cuerpo sube 10 mm más |
| | el papel | — | — |

---

## 10. El orden

1. Papel, versión 1.
2. Junta: el censo, Serrano y Elke.
3. Versión 2.
4. Acta con renders y firma.
5. Plan.
6. Tanda, con su PR y sus issues.
