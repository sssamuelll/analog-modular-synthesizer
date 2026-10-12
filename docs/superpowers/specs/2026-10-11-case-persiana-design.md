# La persiana: el case sin piel, y el costado que respira

**Fecha**: 2026-10-11 · **Estado**: **firmado el 11-10** (versión 2, después de la junta): D-S1 en conversación (*«he decidido C · La persiana»*), y de D-S2 a D-S11 y el papel en el acta, todas en la opción recomendada. **D-S4 en espera**: Samuel la firmó con la nota *«pero ojo, estoy pensando en quitar la tabla, creo que es algo que nos puede beneficiar, que opinas tu?»* (§8). **Implementado el 2026-10-12** en la rama `feat/case-persiana`, del plan `docs/superpowers/plans/2026-10-11-case-persiana.md` (PR #412). **D-S4 firmada después, el 11-10 a las 23:00: quitar la tabla** (ficha `quitar_tabla` del acta). Va en un papel corto y su propia tanda ·
**Sucede a**: `2026-09-05-case-piel-organica-design.md` como dirección del acabado. Su D-P1 (*la piel sustituye a techo, nariz, talón y las dos mejillas*) nunca se firmó ·
**Base**: `main` en `820a2eb` (11-10). Es el case de agosto con lo que la etapa de la piel dejó hecho en el modelo y sigue valiendo: la tabla de 30 con canto redondeado (ficha 12), la tira negra del valle (ficha 6), los paneles vestidos y los rieles plateados (ficha 14) ·
**Se apoya en**: `2026-08-28-costilla-pletina` (el anillo), `2026-08-29-nariz-recta-valle-limpio` (la nariz), `2026-08-29-trasera-capturada-talon-nariz` (la trasera y el talón), `2026-08-30-techo-macizo-chapas-empotradas` (el techo y la rendija del alero, que siguen), `2026-08-31-case-tanda-b` (las tres filas, paneles fijos) y `2026-09-05-fuente-v5-ladrillo` (D-V1, la fuente afuera) ·
**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, el marco de la ventana, los paneles rehundidos, la trasera ámbar ·
**Acta**: https://claude.ai/artifact/UE2d6fVHgeGvFQuzMFHswt («El SAM17 del monje»), con las tres direcciones del 11-10 y, arriba, la persiana después de la junta ·
**Modelo**: `case/cad/persiana.py` (propuesta, no puerta) imprime las cifras de este papel: geometría, aire y peso; con `--json` escribe la geometría por capas para el render. Las cuentas de vibración son de Elke Brandt, con un modelo de vigas fuera del repo (§3.3) ·
**Junta** (11-10): censo de impacto (Amina Halcyon), Adrian Serrano (lo no verificado: 2 BLOCKER, 5 HIGH) y Elke Brandt (fabricación, sujeción y sonido: 1 BLOCKER, 2 HIGH). La versión 1 de este papel tenía cuatro cifras mal y dos imposibles; cada corrección dice de dónde salió.

---

## 0. En una línea

El case se queda sin piel. Vuelve a ser el aluminio de agosto, anodizado en negro, y cada mejilla de acrílico se cambia por una **persiana**: una placa de 6 mm, por fuera del anillo y tapándolo, con 47 varillas rectas y verticales de 2 mm, atadas por dentro en dos alturas, que se pone y se quita con imanes. Es por donde respira el instrumento, y lo único que se ve de él además de los paneles.

---

## 1. Lo que dijo Samuel

El 10-10, en las notas del acta «SAM17 frente al concepto»:

- *«yo creo que por mas que queramos la idea no es igualar el concepto es utilizarlo como inspiracion para crear nuestra propia obra de arte, basada en la sencillez y genialidad de un monje budista zen que ha vivido 30 años estudiando sintetizadores en las montañas de shikoku»* (ficha `corteza2`).
- *«quiero que lo hagamos lo mas simple posible si no se puede igualar el efecto del concepto vamos a crear un concepto nosotros que sea minimalista y elegante»* (ficha `masa2`).

El 11-10, en conversación:

- *«vamos a reimaginar todo esto del case, lo que nos importa es que sea funcional, asi que podria ser hasta brutalista, pero yo espero un poquito de elegancia al mismo tiempo que identidad»*.
- *«hay muchas decisiones que son tomadas en beneficio del instrumento (los tamaños los angulos todo eso esta calculado, de hecho tenemos que meter el row U1 en el valle eso no lo haz todavia simulado con paneles»*.
- *«cuando ponemos masa blanca sobre nuestra estructura se hace como muy grueso y eso se ve como grotesco»*.

El acta del 11-10 le puso tres maneras de dibujar el costado con el mismo cuerpo: el jardín seco, las fuerzas y la persiana. Escogió la persiana: *«he decidido C · La persiana»*.

**Por qué la masa salía gruesa.** Cada vuelta de la piel tenía que envolver un anillo de 14 mm con su holgura, y nunca bajó de 21 a 28 mm de borde. La persiana no envuelve: se apoya en la cara del anillo. De frente, el marco de los paneles es el canto del anillo (14) más el de la persiana (6): **20 mm, todo negro**, con la junta de sombra del chaflán del anillo entre los dos (§4.3). No es más fino que la piel en milímetros; es fino porque no es masa: es una línea negra contra paneles grafito.

---

## 2. Lo que cambia

Contra la base (`820a2eb`):

| | pieza | qué le pasa |
|---|---|---|
| **se va** | las dos mejillas de acrílico naranja de 8 (`costados()`), coplanares en el rebaje del anillo | las sustituye la persiana |
| **entra** | **la persiana**, una por lado | §3 |
| **cambia** | el anillo | **gana diez bolsillos por cara** para los tacos de la persiana (§4). Lo demás, igual: su rebaje se queda vacío y tapado (§7.2) |
| | la nariz y el techo | sus labios bajan hasta el riel y cierran las rendijas de la ficha 6 (§7.3) |
| | el color | todo el aluminio visto, anodizado negro y de una sola aleación (§7.1). Los Z-Rails se quedan plateados: ya están comprados |
| | el ancho por fuera | +12 mm. **`ancho_total` no cambia**: es derivado y mide de anillo a anillo. Hace falta una cota nueva, `ancho_exterior` = `ancho_total` + 2 · 6 = 580,62 (§8) |
| | la tabla | D-S4 (§8) |
| | la puerta del aire | pasa a calcular con cada hueco a su altura y con la fuente v5 (§5) |
| **se queda** | la silueta, las tres filas, los Z-Rails, el marco de la ventana, el talón, la trasera ámbar con el KONDOR y sus 46 ranuras, la rendija del alero, la tapa y la tira del valle | como están |
| **se retira** | la dirección de la piel orgánica | §10 |

---

## 3. La persiana

### 3.1 Qué es

Todas las cifras salen de `python case/cad/persiana.py`.

| | valor | por qué |
|---|---|---|
| contorno | el perfil real del anillo (`perfil_real`: 197 puntos, con los labios del anillo y las éntasis), 0,3 mm sobre la tabla | que su canto caiga sobre el del anillo. Con el perfil de 7 puntos, los labios asomaban hasta 4,1 mm |
| grueso | 6 mm | lo que la sostiene de frente (§3.3) |
| borde macizo | 4 mm | el marco que se ve de lado |
| varillas | **47**, verticales y rectas, de **2,0 mm** | 6 / 2,0 = 3:1, la esbeltez máxima de pared fresada del repo (`ESBELTEZ_MAX_PARED`). La versión 1 decía 1,9: 3,16:1, fuera de la regla |
| ritmo | paso medio **7,0 mm** (ranura de 5,0), con una ola lenta de ±16 % y un ±6 % de azar determinista (k · φ módulo 1, sin `numpy.random`) | como un bambusal. La versión 1 decía 6,2: con el aire bien calculado no pasaba el pesimista (§5) |
| puntas de ranura | radio 1,5, el de la fresa de Ø3 | la fresa no deja esquinas vivas; contra las pendientes se come 3,6 a 4,8 mm de cada punta |
| atados | dos, a 85 y 171 mm del suelo, de 4 mm de alto; ahí la ranura se queda a 4 de los 6 mm y deja un puente de 2 por detrás | **son requisito de taller** (§3.3) y de rigidez; cuestan 782 mm² de aire |
| banda ciega | los 20 mm que caen sobre la cara del anillo (23 en el tramo de atrás): ranura a 4 de fondo, alma de 2 | detrás está el aluminio: ahí la ranura no tiene por qué pasar |
| respira | **18 828 mm²** por costado, detrás de la ventana real | el marco de la ventana llega a 26 mm del perfil en seis tramos y a 30 en el de atrás. La versión 1 medía a 28 uniforme |
| se ve abierto | 65 % del costado | |
| peso | 362 g por costado en aluminio | con la banda ciega y los atados |

> **Corrección 2026-10-12 (revisión final de la tanda):** son **44 varillas** libres entre 45 ranuras. El 47 contaba los centros del ritmo: el primero cae en el borde y el último fuera del perfil. `persiana.py` cuenta ahora de la geometría.

### 3.2 Dónde va

Por fuera del anillo, tapando su cara entera. El anillo deja de verse de lado. De frente, el canto de la persiana (6) va pegado al del anillo (14); entre los dos queda el chaflán de 1,5 × 45° de la silueta del anillo, que se queda como **junta de sombra** y esconde el escalón entre las dos piezas (Elke, H15 de Serrano).

### 3.3 Las varillas largas, el taller y el sonido

La varilla más larga mide 248 mm. Tres cosas, de la junta:

**Sin atados no se fresa.** Con atados, la varilla aguanta de lado 79–80 N/mm a mitad de su vano; sin ellos, 3–5 N/mm. La pasada de acabado empuja 3–10 N (ESTIMADO): sin atados, más de 1 mm de flecha mientras se corta. Los atados no son un adorno ni una opción: sin ellos la pieza no sale.

**Lo que aguanta y cómo suena.** Elke montó un modelo de vigas con la geometría real (las varillas de `sudare.py`, el contorno real, los atados como vigas de 4 × 2) y lo contrastó contra la viga cerrada de la versión 1 (160,5 Hz y 0,337 mm contra 161 Hz y 0,34). En aluminio, E = 69 000 MPa y límite 240 (valores de manual, sin hoja en el repo):

| caso | modo de lado | modo de frente | 10 N de frente | 50 N de lado |
|---|---|---|---|---|
| sin atados, libre desde el borde (la versión 1) | 161 Hz | 507 Hz | 0,34 mm | 429 MPa: se dobla para siempre |
| atados, banda apretada plana contra el anillo | 1 416 Hz | **916 Hz** | 0,031 mm | 148 MPa: vuelve |
| atados, solo el borde apoyado | 1 368 Hz | **347 Hz** | 0,051 mm | 147 MPa: vuelve |

Lo que eso dice: **el primer modo es de frente, entre 350 y 920 Hz, y lo decide cómo se sujete la banda**, no los atados. La versión 1 decía «suena por encima de 1,4 kHz»: era solo el modo de lado. La palanca es la sujeción (§4): la banda plana, con un punto cada 100 mm o menos, lleva el modo hacia 900 Hz. Opcional y sin coste de aire: el puente del atado de 2 a 3 mm sube el modo de frente de 916 a 1 007 Hz. Entre la banda y el anillo no va fieltro ni EPDM: desacopla la banda, baja el tono y suma ancho.

Estas cifras son de la geometría de la versión 1 (1,9 mm a paso 6,2). Con 2,0 a paso 7,0 la varilla es un poco más rígida y el atado un poco más largo; se recalculan en el plan, y lo que decide es la muestra (§3.4).

**El PA12 no aguanta.** Con el mismo modelo: 0,8–2,0 mm de flecha con un dedo de frente, el primer modo entre 90 y 240 Hz, y 148 MPa contra 48 con 50 N de lado: se rompe. Además, la mitad alta de la persiana es la salida del aire caliente (45 °C de sala + 19 K), y las cuentas de PA12 eran a temperatura ambiente (H7). La persiana va en aluminio (D-S2).

### 3.4 La muestra

La del #398 se cambia por **una tira de altura completa**: 60 × 256 mm, cortada de la propia persiana donde están las varillas de 248 (x ≈ 270–330), con 9–10 varillas, los dos atados, la banda ciega, el borde de 4 en los cuatro lados y dos tacos con sus imanes sobre una placa de 14 con dos bolsillos. Mismo material, mismo taller, mismo anodizador. Una muestra de 100 × 100 no sirve: ningún vano pasaría de 45 mm, sería seis veces más rígida y daría verde con autoridad (Elke).

Lo que mide:

- el corte pasante en el vano de 83, sin vibración y con 0,05 mm o menos de ondulación de pared (ESTIMADO);
- el anodizado en cantos de 2 y en el fondo de las ranuras ciegas;
- **el golpe de uña**: el tono más bajo de frente y cuánto dura. Criterio: **que se apague en medio segundo o menos**. Si dura más, una lámina de aluminio con adhesivo viscoelástico (tipo 3M 434/435; la hoja hay que traerla) pegada detrás de los dos atados, que no se ve y no quita aire;
- el tirón de los imanes, con dinamómetro;
- el escalón entre el canto de la persiana y el del anillo, contra el cupón del anillo.

---

## 4. Cómo se sujeta

> **Corrección de la versión 1.** Decía «las fijaciones van por dentro, en la banda maciza de 2 mm». No cabe: en 2 mm no agarra ni un M2 (pide 3–4 mm de rosca), y por dentro no se llega. Desde la tanda B los paneles son **fijos**, la cara interior del anillo la tapa el marco de la ventana hasta 26 mm de la silueta (y atrás, el bolsillo de la trasera), y cada tornillo sería un M3 de 20 mm detrás del último HP de una fila. Limpiar el polvo pediría quitar un panel 3U.

**La propuesta de Elke: tacos e imanes, sin herramienta y sin una cabeza a la vista.**

- **La persiana** lleva **10 tacos** de Ø8 × 3,5 en el dorso, del mismo bloque (sale de pletina de 12, frenteada a 9,5 con los tacos: ninguna pieza suelta), a 7 mm del contorno, uno cada ~96 mm por el perímetro.
- **El anillo** lleva **10 bolsillos** en su cara de fuera, que ahora nadie ve: 3,8 mm de hondo (0,3 de aire bajo el taco) más el asiento del imán, Ø6,1 × 3,1. Quedan 3,0 mm de pared hasta el rebaje vacío del acrílico, que es `PARED_MIN_ANILLO`, y 10 mm o más de cada una de las 14 roscas M4 y de los 3 M5 de la tabla.
- **Dos localizan, ocho retienen.** En el suelo, x = 25: taco redondo en agujero Ø8 H7/g6 (juego de 5 a 29 µm; ISO 286-2, citado de memoria). En el suelo, x = 290: colisa de 8 H7 × 10 en x, que localiza sin forzar. Los otros ocho, Ø9 con holgura, retienen.
- **Imanes**: pares de neodimio N42, Ø6 × 3 en el anillo y Ø6 × 2 en el taco, con la polaridad fija y marcada. En el tramo de atrás, detrás está el bolsillo de la trasera, y van imanes finos (Ø6 × 1) para que la pared no baje de 3,1. Tirón total del orden de **50–70 N** (ESTIMADO; se mide en la muestra) contra una persiana de 3,6 N (362 g). Si se levanta el aparato por los costados, la carga la llevan los tacos, no los imanes.
- **Quitarla**: se tira derecho con dos ganchos de alambre de 2 mm metidos en dos ranuras junto a un atado. Sin la persiana, la ventana del anillo deja aspirar el interior sin quitar paneles.

> **Corrección 2026-10-12 (revisión final de la tanda):** «uno cada ~96 mm» no cabe. Con diez tacos y 10 mm a cada rosca, el tramo más largo sin taco no baja de 106 mm, y con los localizadores en x = 25 y x = 290 queda en **112** (`persiana.py` lo minimiza; antes dejaba 166). Once tacos lo bajan a 92. Lo decide Samuel; mientras, el budget lo declara como HUECO.
- **Alineación**: el canto de la persiana queda a 0,2 mm o menos del del anillo (juego del localizador más las tolerancias de contorno de las dos piezas, ±0,05–0,10 del taller de los anillos). Lo esconde la junta de sombra (§3.2). La arista de atrás de la persiana va rota a 0,3 × 45°.

Las dos salidas que no tocan el anillo rompen un requisito cada una: cinta VHB (no se quita para limpiar) o tornillos M2 negros en el fondo de las ranuras (se quitan, pero se ven, y la ficha 11 pidió que no se viera ninguno). Es D-S3.

Elke colocó los tacos contra las roscas que da hoy `clearance_budget.py`. **El PLIEGO está atrasado en eso**: dice los M5 de la tabla en 44,6 / 153,7 / 262,8 y la M4 del suelo en 236,2, y el budget da 53,3 / 159,9 / 266,5 y 242,76. Lo corrige el plan.

---

## 5. El calor

> **Corrección de la versión 1.** Sus cifras salían de `piel_termica.py`, que pone la entrada de cada costado a un cuarto del alto y la salida a tres cuartos, sea como sea la ventana. La ventana de la persiana es ancha abajo y una cuña arriba: el centro de su área está a 93 mm de 256. Con eso el tiro real es menor, y el pesimista de la versión 1 (17,2 K) era optimista. **Las cifras de la piel salían del mismo modelo y tenían el mismo sesgo.** (H1 de Serrano.)

`persiana.py` calcula con el **plano neutro**: cada hueco a su altura real; lo que queda por debajo del plano entra y lo que queda por encima sale. Con una entrada y una salida da **exactamente** lo que `clearance_budget._tiro()` (el guion lo comprueba al arrancar). Entran las dos persianas, la rejilla baja de la trasera, la rendija del alero y las ondas.

| escenario | W | `C_D` de la puerta (0,65) | pesimista (0,55) | techo |
|---|---|---|---|---|
| **v5 declarada, fuente afuera** | 64,2 | **16,9 K** | **18,9 K** | 20 K |
| v5 + 2 W de luz dentro | 66,2 | 17,2 K | 19,2 K | 20 K |
| v5 + 5 W de luz dentro | 69,2 | 17,7 K | 19,8 K | 20 K |
| fuente adentro (v5 + 25,02) | 89,2 | 21,0 K | 23,5 K | **no pasa** |
| v4, lo que lee hoy `guarda_aire()` | 147,31 | 29,4 K | 32,8 K | **no pasa** |

Y con 64,2 W, pesimista, por partes:

| | salto |
|---|---|
| todo (la tabla de arriba) | 18,9 K |
| las dos persianas solas, sin la trasera ni el alero | 22,7 K |
| **un costado tapado** (el aparato contra una pared) | **26,0 K** |
| sin persianas: el case de agosto | 51,9 K |

Lo que eso dice:

1. **Pasa con la fuente afuera y con 1,1 K de margen en el pesimista.** Por eso el paso es 7,0: con 6,2 daba 20,1 K.
2. **La rendija del alero no muere.** El §7.2 de la piel la daba por muerta; con la persiana es una de las dos salidas altas, y sin ella no pasa. `guarda_rendija()` y su capilaridad siguen.
3. **Los dos costados tienen que quedar libres.** Con uno contra una pared no pasa. Es una **condición de uso** que hoy no está escrita en ningún sitio: va al manual y al pliego, con la holgura que se mida en el arranque (D-S11, HUECO 4).
4. **El #289 no se cierra solo con la persiana.** `guarda_aire()` lee hoy 147,31 W de la v4 (`params.scad:1719`, atado por `guarda_potencia_vigente()` a `hardware/01-power-supply/v4/calor_budget.py`), y con eso no pasa. La fuente v5 mandó cambiar esa cifra a 64,22 y **nadie lo hizo**. Cerrar el #289 son tres cosas: aplicar esa enmienda, mover `guarda_potencia_vigente()` a la v5, y que `_tiro()` calcule con el plano neutro y las persianas. Detrás cuelga una cadena: `calor_budget.py` (`A_EF_BASE_MM2`, `P_BASE`), `test_calor_budget.py`, `TECHO_VENTEO_MM2` de `02-midi-cv/power_budget.py`, `medidas.csv` y `check_bringup.py`, y `canario_techo()`, que exige que el HUECO se publique. Va en el plan, en su orden.
5. **La puerta juzga con el `C_D` de 0,65**; el pesimista es la prueba de robustez. Este papel da los dos y no promete más que el primero.

> **Aplicado el 2026-10-12 (plan del aire, `docs/superpowers/plans/2026-10-11-aire-plano-neutro.md`):**
> `potencia_disipada` = 64,22 W de la v5, `_tiro()` cuenta con el plano neutro y
> las dos persianas, y `guarda_aire()` vuelve a juzgar con `C_D` = 0,65: 16,9 K,
> 18,9 con el pesimista. La fila de la v4 de la tabla es la de antes. Con la sala
> de 45 °C de la spec del chasis serían 18,3 y 20,5 K: la puerta lo publica como
> HUECO hasta que se decida la sala del case. Los 64,22 W son cota de abajo: la
> enmienda M1 de la v5 aísla el +5 V digital y deja su pérdida sin valor. La
> chimenea aguanta 82,9 W con el `C_D` de la puerta y 70,1 con el pesimista, y
> `guarda_aire()` lo imprime en cada corrida.

---

## 6. Los líquidos

> **Nueva, de la junta (H5 de Serrano).** El papel del techo macizo sacó la salida de aire de la meseta por esto: *«esa parte es sensible a que le entren líquidos»*. La persiana abre 45 ranuras por costado, pasantes dentro de la ventana.

Lo que se sabe: los primeros 26 mm sobre la tabla no pasan (detrás están la banda ciega, el anillo y el marco), así que un charco en la mesa no entra. Un derrame que caiga sobre el costado baja por las varillas y **parte entra**: cae sobre el canto de la ventana del anillo, el marco y la tabla. Lo que no se sabe es si llega a alguna placa. **El ensayo de derrame del techo se extiende a los costados** (D-S10): la misma taza, volcada sobre el costado, y el criterio de que nada llegue a una placa. Si no pasa, el rebaje vacío del anillo puede trabajar de canalón con dos desagües abajo; eso se dibuja solo si el ensayo lo pide.

---

## 7. El cuerpo, sin piel

### 7.1 El negro

- **Una sola aleación** para todo el aluminio negro que se ve: **6082-T6/T651**, que ya es la de las chapas. Con la persiana canto con canto con el anillo, dos aleaciones se distinguen en la junta.
- **Un anodizador y un lote.**
- **Arista rota de 0,2 mm o más** en todo canto visto (C0,2 o R0,2). En canto vivo el anodizado no cierra la arista: sale más claro y se pela al limpiar, y serían 94 rayas grises a lo largo de las varillas (ESTIMADO, práctica de taller).
- Espesor: ISO 7599, clase AA15–AA20, sellado (citado de memoria, sin copia en el repo).
- Los contactos del bastidor del anodizador van en el dorso de la banda, que tapa el anillo.
- El PLIEGO dice hoy «anodizado satinado» para el anillo: se reescribe.
- **La tierra.** Con D-V1 la red no entra en el case y no hace falta continuidad de tierra. Si algún día la pide (el hueco H-V5-PE de la fuente), la persiana flota (anodizada y sujeta con imanes) y llevaría un taco enmascarado con un contacto de muelle.

### 7.2 El anillo

Se queda como está firmado, **más los diez bolsillos de cada cara** (§4). Su rebaje, donde asentaba el acrílico, se queda **vacío y tapado** por la persiana. Quitarlo no compra nada y cuesta mucho: los mismos parámetros que lo dibujan (`rehundido_acrilico`, `rebaje_anillo`, `hol_costado`, `entrada_costado_trasero`, `t_cheek`) también son el bolsillo de la trasera, la pata trasera del marco y la tolerancia de la trasera, y `guarda_tramo_trasero()` trabaja con margen cero contra él. El rebaje vacío es un canal de 6 × 11 que va a juntar polvo: con la persiana fuera se aspira.

Lo que muere con el acrílico (H4 de Serrano), y el plan lo resuelve una por una, con su razón:

- `costados()`, `costado_2d()` y su DXF, y `guarda_costado()` de `check_dxf.py`, que sin ese DXF ya no tiene contorno: **se retiran**.
- Lo que sigue sirviendo pero se derivó del acrílico **se re-deriva o cambia de sujeto**: el «14 lo manda el acrílico» de `t_anillo`; las condiciones de `guarda_rebaje()`; el caso de carga de `guarda_marco_ventana()` («el acrílico empujado desde fuera contra el marco», el que puso `marco_fondo_trasera` = 30); el «el costado entra ≥ 3» de `guarda_tramo_trasero()`; el criterio 2 del punto de parada del cupón («el rebaje asienta el PMMA del lote»); y la junta EPDM del costado.
- **Entra una puerta nueva para la persiana**, que hoy no vigila nadie: el aire (plano neutro), la esbeltez de la varilla, que los tacos libren las roscas y la pared de 3, que los imanes sostengan el peso con margen, y que la persiana no toque la tabla.

### 7.3 Las rendijas de la ficha 6

Sin la piel, arriba de la fila alta y abajo de la baja vuelve a verse el ámbar de dentro entre el panel y la chapa. **No es un olvido: las piden dos reglas del barrido de cuando las filas giraban.** `guarda_nariz()` pide al menos 1 mm de aire bajo la cara del riel, y `guarda_retorno_meseta()` pide `holgura_rail` (4 mm) sobre el riel. Desde la tanda B los paneles son fijos: esas dos reglas perdieron su sujeto.

La propuesta de Elke, con las puertas corridas:

- `retiro_placa_inf` de 9 a **11,9**: la nariz llega a 13,48, pisa 0,98 mm de riel y deja 1,02 al panel.
- `retorno_meseta` de 4 a **9**: el techo llega a 146, pisa 1,0 de riel y deja 1,0 al panel.

Siguen en verde `guarda_marco_ventana()`, `guarda_anclajes()`, `guarda_paneles_fijos()` y `guarda_tramo_trasero()`. Caen, por construcción, las dos reglas del barrido, y las sustituye la del labio que ya existe (`LABIO_AIRE_MIN` = 1,0 contra el canto del panel), más 0,5 mm de fondo mínimo contra la cara del riel. Queda 1 mm de sombra con el riel plateado detrás, y el panel sale de frente con 1,0 de holgura. El techo crece 5 mm de desarrollo y la nariz 2,9. Es D-S9.

---

## 8. El ancho y la tabla

`ancho_total` es derivado (largo del riel + holgura + 2 · `t_placa` + 2 · `t_anillo`) y mide de anillo a anillo; z = 0 está en la cara de fuera del anillo izquierdo. La persiana va por fuera: de z = −6 a 0 y de `ancho_total` a `ancho_total` + 6. Entra una cota derivada nueva, **`ancho_exterior` = 580,62**, y se revisa cada uno de los 72 usos de `ancho_total` para ver cuál quería decir «por fuera» (el censo del plan).

**Lo que hizo el plan** (2026-10-11): `ancho_exterior` entra cuando se decida la tabla (D-S4). Hoy no lo lee nadie, y no se crea un parámetro sin lector.

`vuelo_zocalo` se mide desde el anillo. Con 20, la tabla asoma **14 mm a los lados**, por fuera de la persiana, y 20 delante y detrás. D-S4 escoge entre:

- **un solo vuelo de 20**: 14 a los lados, tabla de 608,62 × 359,76; o
- **dos vuelos**, `vuelo_lado` 26 y `vuelo_fondo` 20: 20 en los cuatro lados, tabla de 620,62 × 359,76.

La única regla que vigilaba el vuelo era la regla 3 de `piel_choques.py` (25–40 contra la piel), que muere con la piel. La sustituye una que mide contra la persiana.

**En espera (11-10), y firmada después: quitar** (23:00, ficha `quitar_tabla`). Antes Samuel firmó «uno» y escribió: *«pero ojo, estoy pensando en quitar la tabla, creo que es algo que nos puede beneficiar, que opinas tu?»*. Quitarla es otro papel: hoy la tabla **es el suelo** (en ella van los anillos, la nariz, el talón y las patas, y amarra los dos anillos por abajo), y sin ella hace falta un suelo nuevo. Lo que compra, medido con `persiana.py`: unos 4–5 kg de nogal menos, y la mejor entrada de aire posible, el suelo (con 10 000 mm² abiertos abajo, el pesimista baja de 18,8 a 16,1 K). **Mientras se decide, este papel no toca la tabla**: se queda como está en la base, sin redimensionar.

---

## 9. La luz

De día el costado casi desaparece, y la identidad depende de lo que se ve entre las varillas. Hoy eso es la trasera ámbar iluminada por la sala. **Una luz propia dentro no es una pieza nueva: reabre una retirada.** El papel firmado del instrumento entero retiró en su D1 *«el farol del interior (#42)»* junto con la cadena WS2812. D-S5 es si se reabre: entonces vuelve el #42, la carga entra en el presupuesto de la fuente (`ladrillo_budget.py`, en el riel que se escoja) y en el calor (5 W suben el pesimista de 18,9 a 19,8 K).

De noche, con luz, los dos atados tapan las ranuras en 4 mm por detrás: son **dos rayas oscuras horizontales** que cruzan el ámbar a 85 y 171 mm. Las sudares de verdad tienen sus hilos. Los renders del acta, arriba, ya las llevan.

---

## 10. Lo que se retira

- **La puerta de la piel.** `check_piel.py` mira piezas que no se van a fabricar; `gates.py` la recoge por su nombre, así que sale al borrarla.
- **Los guiones de la piel**: `piel_organica.scad`, `imprimir_piel.py`, `render_piel.py`, `piel_borde.py`, `piel_choques.py`, `celosia*.py` y sus JSON, `kondor_lattice.*`, y los `sam17-piel*.png` versionados con su lista blanca de `.gitignore`. Si se borran o se archivan es D-S7. **Antes hay que mudar tres cosas que la persiana usa**: el contorno real (`PART="perfil_2d"` de `piel_organica.scad` → `piel_borde.py` → `piel_borde.json`, que ninguna puerta regenera), la separación negro/plateado de la ficha 14 (`piel_organica.scad`) y la llamada a `cara_panel.vestir()` (hoy solo la hace `render_piel.py`).
- **`piel_termica.py`** sale también: su modelo de chimenea queda sustituido por el plano neutro de `persiana.py`, y su `placa_ambar` (#392) muere con la piel.
- **La funda** (rama `feat/arreglos-concepto`, tres commits locales que nunca se empujaron) se cierra sin mergear.
- **Los issues**, cada uno con su comentario de previsto contra encontrado: #392 (placa ámbar) y #397 (satinado del PA12) mueren con la piel; #393 (fijaciones por dentro) pasa a ser los tacos e imanes (§4); #398 (pieza de prueba) pasa a ser la tira de altura completa (§3.4); #289 se cierra con la cadena del §5; #395 (la trasera en dos materiales) sigue igual; #42 vuelve solo si D-S5 lo pide.

El censo de la junta, pieza por pieza y línea por línea, es la lista de comprobación del plan: modelo (`sam17_case.scad`, `params.scad`), las gemelas de `clearance_budget.py` y `check_dxf.py`, `export.ps1`, los DXF de `case/plans/`, el PLIEGO, el RFQ, el README, las cuatro specs de agosto que describen la mejilla coplanar y la del 15-08 (que pasa a su revisión 30), y los renders que importan `assembly_acrilico`.

---

## 11. Los renders

La escena del acta pasa al repo como `case/renders/render_persiana.py`: el cuerpo en negro, las dos persianas con sus capas (`persiana.py --json`), la cara de los paneles (`cara_panel.py`) y **la fila del valle con paneles**. Lo que se pinta en el valle (cascos, ocho entradas y salidas, MIDI, reloj y USB) es **provisional**: el reparto lo decide el papel del panel. Vistas: de frente desde la cámara de la imagen 2 del concepto, por detrás, de lado, el costado solo, las dos rendijas de cerca, y de noche con la luz dentro. Los umbrales de brillo y color de `render.py` se calibraron con un case naranja y plateado; el nuevo lleva los suyos.

---

## 12. Lo que Samuel decide

| | decisión | estado |
|---|---|---|
| **D-S1** | el costado es la persiana | **firmada 11-10** — *«he decidido C · La persiana»* |
| **D-S2** | material: **aluminio 6082-T6/T651 fresado y anodizado negro** (recomendado: el PA12 no aguanta, §3.3). **Con esto se retira D-P2** de la piel (*«todo el acabado se hace con impresión 3D»*): la persiana y todo el cuerpo son metal | **firmada 11-10** |
| **D-S3** | la sujeción: **tacos e imanes, y el anillo gana diez bolsillos por cara** (recomendado) — o cinta VHB (no se quita) — o M2 negros en el fondo de las ranuras (se ven) | **firmada 11-10** |
| **D-S4** | la tabla: un vuelo de 20 (14 a los lados) — o dos vuelos, 26 y 20 (20 en los cuatro lados) | **firmada 11-10 («uno»), **en espera**: Samuel piensa quitar la tabla (§8)** |
| **D-S5** | la luz de dentro: reabre D1 del instrumento y el #42 — o no | **firmada 11-10 («no por ahora»)** |
| **D-S6** | lo del valle es provisional y solo de render | **firmada 11-10** |
| **D-S7** | los guiones de la piel se borran — o se archivan (lo que la persiana usa se muda antes) | **firmada 11-10 («se borran»)** |
| **D-S8** | la regla del puente (≥ 0,8 × espesor, `guarda_puentes_ventilacion()`) **no se le aplica a la persiana**: nació para plancha perforada (se dobla al manipularla, y en PMMA arranca la fisura). A la persiana fresada se le aplican la de esbeltez (3:1) y la cuenta de rigidez (recomendado) — o se le aplica, y la varilla pasa a 4,8 mm, que es otra pieza | **firmada 11-10** |
| **D-S9** | las rendijas de la ficha 6 se cierran con la nariz y el techo (§7.3), y las dos reglas del barrido se sustituyen por la del labio | **firmada 11-10** |
| **D-S10** | los líquidos: el ensayo de derrame se extiende a los costados, con el criterio de que nada llegue a una placa (recomendado) — o se acepta el riesgo sin ensayo | **firmada 11-10** |
| **D-S11** | condición de uso: los dos costados libres, con la holgura que se mida en el arranque, escrita en el manual y en el pliego | **firmada 11-10** |

---

## 13. HUECOS

1. **El sonido**, medido en la tira: tono más bajo y duración del golpe de uña. Criterio: medio segundo o menos (§3.4).
2. **El tirón de los imanes**, con dinamómetro en la tira.
3. **La vibración con la geometría final** (2,0 a paso 7,0): el modelo de Elke se corrió con la de la versión 1.
4. **La holgura de los costados**: cuánto aire libre a cada lado hace falta. Con uno tapado no pasa (26 K); con uno a 5 cm de una pared, sin calcular. Se mide en el arranque.
5. **El ensayo de derrame en los costados** (§6).
6. **El `C_D` de una ranura de 5 × 6 mm**: sin medir, como todo el `C_D` del repo. El pesimista lo acota.
7. **Las roscas del PLIEGO**, atrasadas contra el budget (§4).
8. **La tierra**, solo si H-V5-PE la pide algún día (§7.1).

---

## 14. El orden

Papel (este, versión 2) → **firma de D-S2 a D-S11** en el acta → plan, con el censo como lista de comprobación → tanda en el repo con sus puertas y los renders del repo. La cadena del #289 (§5) va en la misma tanda o en la siguiente, según la escriba el plan; lo que no puede es quedarse fuera: sin ella, la puerta del aire sigue publicando un HUECO que la persiana ya pagó.
