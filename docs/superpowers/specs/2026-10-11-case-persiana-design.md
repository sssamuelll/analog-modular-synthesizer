# La persiana: el case sin piel, y el costado que respira

**Fecha**: 2026-10-11 · **Estado**: **propuesta**; **D-S1 firmada en conversación el 11-10** (*«he decidido C · La persiana»*), las demás sin firmar (§10) ·
**Sucede a**: `2026-09-05-case-piel-organica-design.md` como dirección del acabado. Su D-P1 (*la piel sustituye a techo, nariz, talón y las dos mejillas*) nunca se firmó, así que el case firmado sigue siendo el de agosto, y es sobre ese sobre el que trabaja este papel ·
**Se apoya en**: `2026-08-28-costilla-pletina` (el anillo), `2026-08-29-nariz-recta-valle-limpio` (la nariz), `2026-08-29-trasera-capturada-talon-nariz` (la trasera y el talón), `2026-08-30-techo-macizo-chapas-empotradas` (el techo), `2026-08-31-case-tanda-b` (las tres filas) y `2026-09-05-fuente-v5-ladrillo` (la fuente afuera, D-V1) ·
**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, el marco de la ventana, los paneles rehundidos, la trasera ámbar ·
**Acta**: https://claude.ai/artifact/UE2d6fVHgeGvFQuzMFHswt («El SAM17 del monje»): las tres direcciones en render, a la misma cámara, con el cuerpo común ·
**Modelo**: todavía fuera del repo (es propuesta). Los guiones viven en el scratchpad de la sesión del 11-10: `sudare.py` (la persiana, 2D), `escena.py` (el render), `persiana_cuentas.py` (rigidez y frecuencia de las varillas). Las cifras de calor salen de `case/cad/piel_termica.py` del repo, con `PIEL_RAMA` apuntando a las medidas de la persiana. Entran al repo con el plan, después de la firma.

---

## 0. En una línea

El case se queda sin piel. Vuelve a ser el aluminio de agosto, anodizado en negro, y cada mejilla de acrílico se cambia por una **persiana**: una placa de 6 mm, por fuera del anillo y tapándolo, con 52 varillas rectas y verticales de 1,9 mm. Es por donde respira el instrumento, y lo único que se ve de él, además de los paneles.

---

## 1. Lo que dijo Samuel

El 10-10, en las notas del acta «SAM17 frente al concepto»:

- *«yo creo que por mas que queramos la idea no es igualar el concepto es utilizarlo como inspiracion para crear nuestra propia obra de arte, basada en la sencillez y genialidad de un monje budista zen que ha vivido 30 años estudiando sintetizadores en las montañas de shikoku»* (ficha `corteza2`).
- *«quiero que lo hagamos lo mas simple posible si no se puede igualar el efecto del concepto vamos a crear un concepto nosotros que sea minimalista y elegante»* (ficha `masa2`).

El 11-10, en conversación:

- *«vamos a reimaginar todo esto del case, lo que nos importa es que sea funcional, asi que podria ser hasta brutalista, pero yo espero un poquito de elegancia al mismo tiempo que identidad»*.
- *«hay muchas decisiones que son tomadas en beneficio del instrumento (los tamaños los angulos todo eso esta calculado, de hecho tenemos que meter el row U1 en el valle eso no lo haz todavia simulado con paneles»*.
- *«cuando ponemos masa blanca sobre nuestra estructura se hace como muy grueso y eso se ve como grotesco»*.

El acta del 11-10 le puso tres maneras de dibujar el costado con el mismo cuerpo: el jardín seco (líneas que se tuercen alrededor de tres piedras ámbar), las fuerzas (las isostáticas del costado, calculadas) y la persiana. Escogió la persiana: *«he decidido C · La persiana»*.

**Por qué la masa salía gruesa, y por qué esto no.** Cada vuelta de la piel (rollo, corteza, funda) tenía que envolver un anillo de 14 mm con su holgura, y por eso nunca bajó de 21 a 28 mm de borde. Lo único que puede ser fino es lo que no envuelve nada. La persiana no envuelve: se apoya en la cara del anillo, y de frente su canto mide 6.

---

## 2. Lo que cambia

Contra el case firmado (el de agosto, con la tanda B del 31-08):

| | pieza | qué le pasa |
|---|---|---|
| **se va** | las dos mejillas de acrílico naranja de 8 (`costados()`), coplanares en el rebaje del anillo | las sustituye la persiana |
| **entra** | **la persiana**, una por lado | §3 |
| **cambia** | el color | todo el aluminio anodizado en negro (anillos, marco de la ventana, nariz, techo, talón, tapa y tira del valle). Los Z-Rails se quedan plateados: ya están comprados |
| | el ancho | +12 mm: la persiana va por fuera del anillo (568,62 → 580,62 por fuera de las dos) |
| | la tabla | vuela 20 en vez de 40 (D-S4), con la losa de 30 y el canto redondeado de la ficha 12 |
| **se queda** | anillos, marco de la ventana, Z-Rails, nariz, techo, talón, la trasera ámbar con el KONDOR y sus ranuras, la tapa y la tira del valle | como están firmados |
| **se retira** | la dirección de la piel orgánica: cubierta, cachetes, corteza, borde, funda | §8 |

---

## 3. La persiana

**Qué es.** Una placa por costado:

| | valor | por qué |
|---|---|---|
| contorno | el perfil real del anillo (`perfil_real` de `piel_borde.json`: 197 puntos, con los labios del anillo y las éntasis de las pendientes), 0,3 mm sobre la tabla | que su canto caiga justo sobre el del anillo. Con el perfil de 7 puntos, los labios del anillo asomaban hasta 4,1 mm |
| grueso | 6 mm | el fondo de la varilla es lo que la sostiene de frente (§3.1) |
| borde macizo | 4 mm | el marco que se ve de lado |
| varillas | 52, verticales, rectas, de 1,9 mm | ninguna se tuerce |
| ritmo | paso medio 6,2 mm, con una ola lenta de ±16 % y un ±6 % de azar con semilla fija | como un bambusal: ninguna caña está a la misma distancia de la otra, pero el ritmo se lee |
| dónde va | por fuera del anillo, tapándolo entero | el anillo deja de verse de lado. De frente se ven su canto de 14 y el de la persiana, 6 |
| respira | **17 671 mm²** por costado con los dos atados (§3.1), dentro de la ventana, a ≥ 28 mm del perfil | §4 |
| peso | 377 g por costado en aluminio, 141 g en PA12, con la banda ciega y los atados | medido sobre el dibujo |

### 3.1 Las varillas largas, y los atados

`persiana_cuentas.py` trata cada varilla como una viga empotrada en las dos puntas (nace y muere en el borde de la misma placa), con la carga en el centro. **Los materiales llevan valores de manual, sin hoja en el repo**: 6061-T6 con E = 69 000 MPa y límite 240 MPa; PA12 impreso con E = 1 800 MPa y 48 MPa.

La más larga mide **248 mm**. Sin nada que la ate:

| | aluminio | PA12 impreso |
|---|---|---|
| un dedo (10 N) de frente | cede 0,34 mm, 27 MPa | **cede 12,9 mm** |
| una mano (50 N) de frente | cede 1,7 mm, 136 MPa: vuelve | se dobla para siempre |
| 10 N de lado (una palanca, un cable que se engancha) | cede 3,4 mm, 86 MPa: vuelve | se dobla para siempre |
| 50 N de lado | **se dobla para siempre** (429 MPa) | se dobla para siempre |
| a qué suena (primer modo) | **161 Hz** de lado, 507 Hz de frente | 42 Hz de lado |

Las dos cosas que eso dice: en nylon, una persiana de varillas sueltas no aguanta un dedo; y en aluminio aguanta, pero **suena dentro de lo que se oye**, como una lámina de kalimba que alguien golpea.

**La salida es la de una sudare de verdad: los atados.** Las cañas de una persiana de bambú van cosidas con hilos horizontales. Aquí son dos puentes por dentro, a un tercio y a dos tercios del alto, de 4 mm de alto: en ellos la ranura no atraviesa, se queda a 4 de los 6 mm de fondo y deja 2 mm de puente por detrás. De fuera no se ven: se mira al fondo negro de la ranura, como en el resto. Con ellos el vano baja a 83 mm:

| con dos atados | aluminio | PA12 impreso |
|---|---|---|
| un dedo (10 N) de frente | cede 0,01 mm | cede 0,48 mm |
| a qué suena, de lado | **1 446 Hz** | 382 Hz |

Los atados cuestan 752 mm² de aire por costado (18 424 → 17 671), y el margen pasa del 35 al 29 %.

### 3.2 La banda sobre el anillo, y por dónde se sujeta

Los 20 mm de la persiana que caen sobre la cara del anillo no necesitan ranura pasante: detrás está el aluminio del anillo. Ahí las ranuras se cortan **ciegas**, a 4 de los 6 mm. De fuera se ven igual (el fondo es negro, como el del resto), y por detrás queda una **banda maciza** de 2 mm por todo el contorno. Ahí van las fijaciones: **por dentro**, sin una cabeza a la vista, como pidió la ficha 11 del acta del 09-10. Cuántas, de qué tipo (rosca en la banda o inserto) y si el destornillador llega desde dentro con los módulos puestos es el HUECO 1.

---

## 4. El calor

`case/cad/piel_termica.py` es la chimenea de la piel: la mitad baja de cada costado entra, la mitad alta sale, más la rejilla baja de la trasera. La física es la de `clearance_budget._tiro()`, y vale igual para la persiana: lo que cambia es cuánto respira. Con los dos atados (17 671 mm² por costado):

| escenario | W | salto, `C_D` de la puerta | pesimista | techo |
|---|---|---|---|---|
| v5 declarada, fuente afuera | 64,2 | 15,4 K | **17,2 K** | 20 K |
| v5 + 2 W de luz dentro | 66,2 | 15,7 K | 17,5 K | 20 K |
| v5 + 5 W de luz dentro | 69,2 | 16,2 K | 18,1 K | 20 K |

Sin los atados, la fuente afuera da 15,0 / 16,8 K y la fuente adentro (89,2 W) 18,7 / **20,9 K**: con la persiana tampoco pasa el pesimista con la fuente dentro. D-V1 sigue como está firmada. **Y el #289 se cierra por la persiana** el día que entre en el modelo con `guarda_aire()` en verde: el venteo que pedía lo paga el costado.

---

## 5. El cuerpo, sin piel

- **Negro.** Anillos, marco de la ventana, nariz, techo, talón, tapa y tira del valle: anodizado negro. Los Z-Rails, plateados. Los paneles, grafito (ficha 14).
- **El anillo no se toca** (D-S3, recomendado). Se queda fresado como está firmado. El rebaje donde asentaba el acrílico queda sin sujeto y tapado por la persiana: no estorba, y quitarlo mueve la pared que comparte con el bolsillo de la trasera (`guarda_tramo_trasero()`) sin comprar nada que se vea.
- **Vuelven las rendijas de la ficha 6.** Sin la piel, arriba de la fila alta y abajo de la baja, entre el canto del panel y la chapa, se ve el ámbar de dentro: es la línea naranja de los renders de frente. La piel las cerraba cayendo sobre el riel; ahora lo tiene que hacer el labio del techo y la nariz, sin estorbar a los paneles al salir (`guarda_paneles_fijos()`). HUECO 2.
- **El valle**: la tira negra de la ficha 6 sigue tapando la esquina de P3.

---

## 6. La tabla

Vuela **20 mm** (D-S4) en vez de los 40 de la ficha 12. Samuel marcó «menos» en el acta del 10-10, contra una propuesta de 30. Sigue la losa de 30 con el canto de arriba redondeado. La regla de la piel que la vigilaba (*la tabla asoma de la piel entre 25 y 40*, `piel_choques.py`) muere con la piel; la que la sustituya mide contra la persiana.

---

## 7. La luz

En la persiana, de día el costado casi desaparece y la identidad depende de la luz de dentro: el ámbar que se ve entre las varillas. Hoy ese ámbar es la trasera iluminada por la sala. **Una luz propia dentro** (una tira de LED) es D-S5. Cuesta lo que dice §4: 5 W suben el pesimista de 17,2 a 18,1 K. Dónde va la tira y de qué carril come no lo dibuja este papel.

---

## 8. Lo que se retira

La dirección de la piel deja de serlo. Lo que en el repo solo existe por ella:

- **La puerta.** `check_piel.py`, que `gates.py` recoge por su nombre, mira piezas impresas que no se van a fabricar. Una puerta que vigila un sujeto muerto no protege nada: sale de `gates.py` en la misma tanda que entre la persiana.
- **Los guiones de la piel**: `piel_organica.scad`, `imprimir_piel.py`, `render_piel.py`, `piel_borde.py`, `piel_choques.py`, `celosia*.py` y sus JSON. Si se borran o se archivan es D-S7. `piel_borde.json` no se va sin más: el perfil real (`perfil_real`) lo usa la persiana, así que esa exportación pasa a un guion propio.
- **`piel_termica.py`** no se retira: es la chimenea, y la persiana la usa. Cambia lo que lee (las medidas de la persiana en vez de `celosia_placa.json`).
- **La funda** (rama `feat/arreglos-concepto`, tres commits locales, nunca empujados) se cierra sin mergear.
- **Los issues** (los cambia el plan, cada uno con su comentario de previsto contra encontrado): #392 (placa ámbar detrás de la celosía) y #397 (satinado del PA12) mueren con la piel; #393 (fijaciones por dentro) pasa a ser el de la persiana (HUECO 1); #398 (pieza de prueba de la esquina) pasa a ser una muestra de persiana: un trozo de 100 × 100 con un atado y la banda ciega; #289 se cierra por §4; #395 (la trasera en dos materiales) sigue igual.

El censo completo de lo que toca, pieza por pieza y puerta por puerta, va con el plan.

---

## 9. Los renders

La escena del acta pasa al repo como `case/renders/render_persiana.py`: el cuerpo de agosto en negro, las dos persianas, la cara de los paneles (`cara_panel.py`) y **la fila del valle con paneles**, que hoy sale lisa. Lo que se pinta en el valle (cascos, ocho entradas y salidas, MIDI, reloj y USB) es **provisional**: el reparto de verdad lo decide el papel del panel (`panel-pantalla-al-centro` §5.1). Cinco vistas: de frente desde la cámara de la imagen 2 del concepto, por detrás, de lado, de noche con la luz de dentro, y el costado solo.

---

## 10. Lo que Samuel decide

| | decisión | estado |
|---|---|---|
| **D-S1** | el costado es la persiana (C del acta del 11-10) | **firmada 11-10** — *«he decidido C · La persiana»* |
| **D-S2** | material de la persiana: **aluminio 6061 fresado y anodizado negro** (recomendado: con los atados es rígido, suena por encima de 1,4 kHz y es el mismo material que el cuerpo), o **PA12 impreso** teñido de negro (más barato; depende de los atados para aguantar un dedo, y D-P2 seguiría valiendo) | pendiente |
| **D-S3** | el anillo no se toca: se queda fresado como está firmado, con su rebaje tapado (recomendado) — o se simplifica sin rebaje | pendiente |
| **D-S4** | la tabla vuela 20 | pendiente (acta del 11-10, ficha «tabla») |
| **D-S5** | la luz de dentro | pendiente (acta del 11-10, ficha «luz») |
| **D-S6** | lo que se pinta en el valle es provisional y solo de render | pendiente (acta del 11-10, ficha «valle») |
| **D-S7** | los guiones de la piel se borran del repo — o se archivan en una carpeta | pendiente |

---

## 11. HUECOS

1. **Las fijaciones por dentro.** Cuántas, dónde en la banda maciza, rosca o inserto, y si el destornillador llega desde dentro con los módulos puestos. Sin dibujar.
2. **Las rendijas de la ficha 6** con las chapas: cuánto se alarga el labio del techo y la nariz, contra la salida de los paneles. Sin dibujar.
3. **El `C_D` de una ranura de 4,3 × 6 mm.** Sin medir, como todo el `C_D` del repo. El pesimista lo cubre con el 29 % de margen.
4. **Lo que suenan las varillas.** Es la cuenta de una viga empotrada, sin medir. Con los atados, en aluminio, por encima de 1,4 kHz. La muestra del #398 lo dice con un golpe de uña.
5. **El polvo.** De lado se ve un 63 % abierto, y atraviesa de verdad el 42 % del costado (22 185 mm²). La trasera ya lo aceptó con sus ranuras; aquí es más, y se dice.
6. **El ancho, +12 mm.** Lo que lo note en el modelo (la tabla, el embalaje, el pliego) sale del censo del plan.

---

## 12. El orden

Papel (este) → junta (Elke Brandt sobre cómo se fabrica, se sujeta y suena; Adrian Serrano sobre lo que este papel no verificó) → firma de D-S2 a D-S7 → plan → tanda en el repo, con sus puertas (el aire, que nada choque, la persiana sobre el anillo) y los renders del repo.
