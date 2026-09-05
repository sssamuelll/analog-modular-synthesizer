# La piel orgánica: cinco pieles a una, y las mejillas que respiran

**Fecha**: 2026-09-05 · **Estado**: **propuesta**; **D-P2 firmada en conversación el 05-09** (*«todo el acabado se hace con impresión 3D»*), y el lenguaje de la piel dicho por Samuel el mismo día mirando el primer render: *«la piel con esa forma orgánica que parece modernista y parecen ramas de árbol»* (§4.1); D-P1, D-P3, D-P4 y D-P5 sin firmar (§12) ·
**Sucede a**: nada; **se apoya en** `2026-08-28-costilla-pletina` (el anillo), `2026-08-29-trasera-capturada-talon-nariz` (la trasera, que se queda), `2026-08-30-techo-macizo-chapas-empotradas` (el techo, que se va), `2026-08-31-case-tanda-b` (las tres filas, que no se tocan) y `2026-09-05-fuente-v5-ladrillo` (la fuente afuera, que este papel reabre en §7.1) ·
**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, el marco de la ventana, los paneles rehundidos, la tabla, el ámbar ·
**Referencia visual**: tres renders de concepto generados por Samuel el 05-09, en `docs/images/case-piel-organica/`. **Mandan sobre lenguaje, no sobre cotas** — la misma regla que el board del 16-08 y la foto del 26-08. Samuel, sobre ellos: *«lo que está en los paneles es conceptual pero se entiende que va con el diseño que estamos haciendo, lo del valle seguimos trabajándolo como veníamos [...] son módulos de la fila B»* ·
**Modelo**: `case/cad/piel_organica.scad` (al lado de `sam17_case.scad`, sin tocarlo), `case/cad/celosia.py` → `celosia_ramas.scad`, `case/renders/render_piel.py` → `sam17-piel*.png`.

---

## 0. En una línea

El case de hoy es **dos anillos de aluminio fresado** —el hueso— con **seis pieles** encima: el techo de chapa, la nariz, el talón, las dos mejillas de acrílico en bolsillo, y la trasera de PMMA. Esto cambia **cinco de esas seis pieles por una** —una piel orgánica impresa que envuelve el canto y forma las mejillas como celosía abierta— y deja el hueso y la trasera donde están.

Lo que compra no es estética: **la ventilación deja de ser un agujero que esconder y pasa a ser la identidad del aparato.** Con las mejillas en celosía, el case pasa el techo de 20 K con el `C_D` pesimista — la primera geometría que lo hace en tres días de barridos — y lo hace con el suelo macizo, el techo macizo y **la fuente dentro o fuera, las dos** (§4.3).

---

## 1. El concepto, leído como plano

Tres renders. Lo que en ellos es decisión y lo que es ruido del generador lo dijo Samuel, y se transcribe arriba.

| render | lo que enseña | lo que de ahí se toma |
|---|---|---|
| `concepto-1-ambar.jpg` | piel blanca orgánica, mejillas en celosía abierta, dos caras de acrílico ámbar, base de madera, una barra entre los dos pisos | la piel, la celosía, la madera. El ámbar en las caras **no**: el render 2 lo mueve |
| `concepto-2-paneles.jpg` | las caras pasan a **paneles de aluminio oscuro** con los controles reales —perillas, faders, la pantalla de 7"—; el ámbar queda **dentro**, como luz por la celosía; tres bloques separados en el panel de abajo | los paneles de aluminio; el ámbar como interior; **los tres bloques son módulos de la fila B** (Samuel). La barra: es el valle, y el valle sigue como venía — y en `sam17-piel.png` la tapa de aluminio del valle entre dos paneles oscuros se lee exactamente así, sin haberla dibujado |
| `concepto-3-trasera.jpg` | atrás: acrílico ámbar con el KONDOR en relieve y las ondas; debajo, una franja de metal con los conectores; debajo, la rejilla de ranuras a todo lo ancho; un IEC a la derecha | **la trasera se queda** —es la del 29-08, en ámbar—; la franja de conectores en metal (§5); las ranuras se quedan (§7.3). **El IEC es una decisión, no un detalle** (§7.1) |

La piel, en los tres, hace lo mismo: envuelve el canto de arriba, forma la nariz y el talón, y en los extremos se abre en celosía. Es «el marco es perfil, no banda», hecho en otro material.

---

## 2. Lo que cambia en el case firmado

| | pieza | papel | qué le pasa |
|---|---|---|---|
| **se va** | techo de chapa + rendija del alero | 30-08 | la piel es el techo. La salida de aire son las mejillas |
| | nariz y talón | 29-08 | la piel es la nariz y el talón |
| | mejillas de acrílico en bolsillo | 28/29-08 | la piel es la mejilla, y respira |
| | **todo el venteo del #289** | 03/04-09 | lo pagan las celosías solas, con margen (§4.3) |
| **se queda** | la silueta de dos pisos, las tres filas, el valle de 55 | 31-08 | igual |
| | Z-Rails, marco de la ventana, paneles rehundidos 1,5 | 29/31-08 | igual |
| | **la trasera**: PMMA, KONDOR, ondas, ranuras, capturada en bolsillo | 29-08 | igual, con la franja de conectores debajo (§5) |
| | la tabla del carpintero, con su vuelo de 10 | 27-08 | igual; sigue asomando 4 mm por fuera de la piel |
| | el ámbar | 27-08 | se queda, pero **dentro**: es la trasera y lo que se ve por la celosía |
| **cambia** | los dos anillos | 28-08 | siguen siendo el hueso. Hoy son pletina de 14 fresada con cara vista de 20 y chaflán **porque se ven**; bajo la piel no se ven, y pasan a **pletina cortada y listo** (§6) |
| | el chasis del PSU | 18-08 | con la fuente afuera (v5) no hay chasis. Si se queda dentro, entra como hoy, por el frente |

El case crece **12 mm de ancho** (6 de piel por lado: 568,62 → 580,62) y nada en alto ni en fondo. La tabla, con su vuelo de 10, sigue siendo lo más ancho del aparato.

---

## 3. La piel

### 3.1 Geometría (lo que está en el modelo)

- **Espesor 6 mm** (`piel_e`). Para nylon MJF, 4–8 es lo normal; 6 deja nervios de 4 en la celosía con carne.
- **Envuelve el canto**: la banda sigue el contorno del anillo (`perfil_lateral()`, con sus chaflanes y radios) 6 mm por fuera, de nariz a talón pasando por el techo. Por debajo no hay piel: ahí está la tabla (`piel_aire` = 0,3 sobre y = 0).
- **Los labios de los extremos** pisan cada panel hasta la placa de anclaje y **no más** (`piel_solape` = `t_placa` = 6): 20 mm de piel sobre cada extremo de cada fila. Más allá estorbaría al módulo al salir — las dos filas son tapa, y nada fijo junto a un riel puede taparle el barrido. Entre los labios la banda se abre entera sobre las tres filas: entre filas no hay piel, como hoy no hay chapa; ahí están la tapa del valle y los rieles.
- **La ventana de la trasera**: el campo visible de hoy (`trasera_campo()`, del labio del talón al del techo), entre los anillos. La piel hace de marco arriba y abajo, como hoy lo hacen las chapas.
- Los paneles quedan **7,5 mm** dentro del plano de la piel (6 de piel + 1,5 de rehundido). En el concepto se leen así: paneles duros dentro de un marco blando.

### 3.2 Material: la única pregunta de estructura (D-P2 — firmada)

> **Firmada el 05-09, en conversación:** *«eso toca decidirlo, todo el acabado se hace con impresión 3D»*. Es **A**. La piel se imprime, y **la pieza impresa es el acabado**: no hay fundición, no hay mecanizado de la piel, y lo que salga de la máquina es lo que se ve. Eso convierte el material en el siguiente parámetro —blanco de impresión (PA12 W) o teñido, resina o nylon— y hace de las dos preguntas de §8 (la costura de la banda, la sujeción al hueso) ingeniería con proceso conocido en vez de opciones. B se queda escrita abajo como lo que se descartó y por qué, no como alternativa viva.

**A. La piel es piel.** Nylon impreso (MJF PA12, o resina) sobre los anillos de hoy, que se esconden. La estructura no cambia: los anillos cargan, el marco de la ventana ata los rieles, la piel se cuelga de ellos. Riesgo cero en lo que ya está calculado. Los paneles de aluminio hacen de disipador (§4.4).

**B. La piel es aluminio fundido** y hace de hueso y de disipador a la vez. Más pesada, molde, más cara — y la versión de serie si algún día hay serie.

**Recomendación: A**, para la pieza de concepto y como base. B se decide con una unidad vendida, no antes. Y con A hay una cosa que no se puede olvidar: **a 45 °C de sala más 14–17 K dentro, un nylon impreso aguanta como piel y no como estructura**. Por eso A exige que el hueso siga.

---

## 4. La celosía

### 4.1 Por qué por guion y no a mano

Del dibujo orgánico importan tres números —cuánto abre, cuánto nervio le queda, cuánto borde macizo la enmarca— y los tres tienen que ser **parámetros**, porque el primero lo lee el modelo térmico y los otros dos los leerá la rigidez. Un dibujo no tiene parámetros.

**Tres versiones en un día, y las tres por mirar el render con Samuel.**

1. **Celdas de Voronoi** (`2bce743`): parametrizable, medible, y **leía a panal**.
2. **Ramas por colonización de espacio** (`d78c592`), tras *«parece modernista y parecen ramas de árbol»*: salió un árbol — ramas sueltas que se cruzan. *«No está ni cerca.»*
3. **Fibras de un campo de flujo** — la de ahora. La referencia es el cuarto render de Samuel, el despiece: el cachete son **nervios largos que nacen del rincón de abajo-delante, se abanican hacia arriba-atrás, se parten y se vuelven a juntar dejando huecos en forma de lente**, escalonados en hiladas. Eso no es un árbol ni un teselado: es un campo de flujo, y `celosia.py` lo genera como tal:

- un **campo de direcciones** sobre el perfil: abanico desde un foco por delante y por debajo del case, ondulado para que las fibras se curven, y enderezándose hacia arriba con la altura;
- **líneas de flujo espaciadas** (Jobard & Lefer, 1997): se integra una fibra por el campo, se siembran vecinas a `SEPARACION` a cada lado, y una fibra muere cuando se acerca a otra. Donde el abanico se abre nacen fibras entre las viejas; donde se cierra, mueren;
- **las lentes con punta** no salen de peldaños: salen de fibras vecinas que convergen y luego se separan. Se modula la dirección con una onda a lo largo del flujo por otra a través de él (período `2 × SEPARACION`): fibras contiguas giran en sentidos opuestos, se acercan hasta que una muere **soldada** en la otra, y más adelante nace otra entre las dos;
- **ninguna punta suelta**: cada extremo que no muere en el marco se suelda a la vecina con una curva tangente al flujo; y **puentes** en S cada `LENTE` mm donde dos fibras corren paralelas mucho rato, que es lo que atiranta la celosía de través.

Los números de arranque salen de la referencia, medidos a ojo sobre la imagen (está en perspectiva: son proporciones, no cotas): nervio ~1/60 del alto del cachete, separación ~1/16, lentes de 3 a 6 separaciones, marco ~1/15. Sobre 256 mm de alto: nervio ~4, separación ~15, lentes 50–90, marco ~17.

| parámetro | valor | qué es |
|---|---|---|
| `MARCO` | 17 mm | marco macizo alrededor de la celosía, desde el perfil |
| `SEPARACION` | 13 mm | entre ejes de fibras vecinas |
| `NERVIO` | 4,2 mm | grosor de la fibra |
| `FOCO` | (−140, −160) | de dónde sale el abanico; lejos, o abajo son rendijas y arriba huecos |
| `ONDA_A` / `ONDA_L` | 11° / 150, 110 mm | ondulación de las fibras |
| `GIRO_ARRIBA` | 14° | las fibras se enderezan al subir |
| `LENTE_MOD` / `LENTE_L` | 11° / 80 mm | la modulación que hace las lentes |
| `LENTE` | 110 mm | entre puentes |
| `CIERRE` | 2 mm | radio del cierre que suelda uniones (`.scad`) |
| `SEMILLA` | 17 | |

Salen **27 fibras, 131 soldaduras, 6 puentes**. Cuatro pasadas en preview 2D de segundos cada una (`celosia.py --preview`): la primera tenía el foco cerca y abanicaba de más; la segunda, lentes tímidas y puntas sueltas. Lo que se afina mirando, con Samuel delante: separación y nervio (la densidad del tejido), `LENTE_MOD` (cuánta punta tienen las lentes) y el marco.

### 4.2 Dos áreas, y por qué no son la misma

La celosía abre desde 17 mm del perfil hacia dentro: eso es **lo que se ve**. Pero detrás de la mejilla está el anillo (20 de cara) y el marco de la ventana (hasta `marco_fondo` = 26 del perfil), y las celdas que caen sobre ese metal no respiran: enseñan aluminio. **Lo que respira es lo abierto sobre la ventana del anillo.**

| por mejilla | mm² | del perfil (52 658) |
|---|---|---|
| región de la celosía (a ≥ 17 del perfil) | 36 266 | 69 % |
| **abierto, lo que se ve** (nervios descontados) | **24 504** | **46,5 %** |
| **abierto sobre la ventana, lo que respira** (a ≥ 26) | **19 367** | **36,8 %** |

Medido por muestreo (120 000 puntos), con cada nervio como cápsula de su grosor. (Las celdas de Voronoi respiraban 22 021 y las ramas 23 809: las fibras son un tejido más cerrado, y se nota abajo.) Dos cosas que el número no lleva y se declaran: el cierre morfológico del `.scad` rellena horquillas y quita algo más (< 2 %), y `marco_fondo_trasera` es 30 y no 26 — se usa 26 en todo el contorno, 4 mm optimista en el tramo trasero.

Visualmente, el anillo detrás de los huecos del borde **no es un defecto**: es la opción A hecha visible — ramas blancas sobre aluminio en la orilla, sobre el ámbar del interior en el centro.

### 4.3 Lo que le pasa al calor

Con `clearance_budget._tiro()` —el modelo de `guarda_aire()`— y las dos mejillas como chimenea: la mitad baja de cada una entra, la mitad alta sale, centroides a un cuarto y tres cuartos del alto; más la rejilla baja de la trasera, que el concepto conserva. Techo, 20 K sobre una sala de 45 °C. `C_D` = 0,65 el de la puerta, 0,55 el pesimista.

| escenario | W | salto | pesimista | sin la rejilla trasera |
|---|---|---|---|---|
| **v5 declarada, fuente afuera** | 64,2 | **14,9 K** | **16,6 K** | 16,4 K |
| v5 a censo | 35,1 | 9,9 K | 11,1 K | 11,0 K |
| **fuente ADENTRO** (v5 + los 25,02 que se irían) | 89,2 | **18,5 K** | **20,7 K** | 20,4 K |
| *hoy, para comparar* | 64,2 | 45,6 K | 51,0 K | — |

Área efectiva **16 752 mm²** (hoy 3 299), tiro **118 mm** (hoy 105).

Tres lecturas:

1. **Es la primera geometría que pasa con el `C_D` pesimista.** Ni la trasera agrandada, ni el suelo ranurado, ni la rendija ancha lo conseguían (v5 §6): la mejor daba 21,0 K. Ésta da 16,6, y con el suelo y el techo macizos.
2. **La rejilla baja de la trasera vale 1,5 K** (14,9 con ella, 16,4 sin ella, mismo `C_D`). Poco, pero no nada: se queda o se va por identidad (§7.3), y si se va, se sabe lo que cuesta. *(La primera versión de este papel decía 0,3 K: restaba la columna pesimista con rejilla a la columna normal sin rejilla — dos corners distintos, el error de siempre. Corregido.)*
3. **Con la fuente adentro ya NO pasa en pesimista**: 18,5 K con el `C_D` de la puerta, **20,7 con el exigente**, contra 20. Con las ramas pasaba (18,3); el tejido de fibras respira 4 400 mm² menos por cachete y ese margen se fue. Ver §7.1.

Lo que el modelo NO cuenta y se declara: la pared exterior (`U_PARED` = 3, sin medir, fuera del veredicto); el `C_D` de una celosía de nylon de 6 mm con celdas de ~25 × 40 (no es el de una ranura en PMMA de 8; probablemente **mejor**, porque la celda es ancha respecto a su profundidad — pero sin medir); y la resistencia de un camino de aire que entra por un extremo, cruza 540 mm de módulos y sale por el otro. Con dos mejillas simétricas el aire entra y sale por la misma, y ese camino es corto; el modelo lo trata como una chimenea y es una aproximación de orden de magnitud. **Se mide en el paso 7 del bring-up, como todo lo demás.**

### 4.4 Y los paneles de aluminio, de regalo

De los 64,2 W declarados, **27,5 están concentrados** en dos o tres placas —los convertidores DC-DC (8,0), la quema de la cascada (5,1) y los cuatro N657 (14,5)— y **36,7 repartidos** en dieciséis placas de voz, la fila de abajo y la pantalla. Lo repartido va por aire. Lo concentrado se puede **atornillar a metal**, y con los paneles de aluminio del concepto el metal ya está: del orden de 0,2 m² a la vista *(ESTIMADO)*, suficiente para sacar esos 27,5 W por conducción a 30 K sobre la sala con h = 6. Los dos caminos a la vez, ninguno forzado. **No está en el modelo** y no se cuenta en §4.3: es margen.

---

## 5. La trasera

Se queda tal cual está firmada el 29-08: PMMA capturado en los bolsillos de los anillos, KONDOR en relieve, las dos ondas, las 46 ranuras. En el concepto aparece en ámbar y no en PMMA claro o ahumado: color de mirar, no cota; el `.scad` no lo fija.

Lo que el concepto añade y tiene sentido: **una franja de metal con los conectores, debajo del acrílico.** Es lo que pedían los hallazgos del 23-08 —los conectores en metal, no en el PMMA— y parte la trasera en dos materiales con dos trabajos: arriba lo que se enseña, abajo lo que se enchufa. No está modelada: es una enmienda al papel de la trasera cuando esto se firme, no un dibujo de este.

**El IEC del render no está decidido.** Con la fuente afuera (v5) ahí va un jack de DC. Con la fuente adentro, un IEC. Es D-V1, y §7.1 dice lo que este case le hace.

---

## 6. El hueso

**Sigue.** Los dos anillos cargan; el marco de la ventana ata los seis rieles y retiene hacia dentro; los Z-Rails llevan los paneles. Nada de eso lo toca la piel.

Lo que sí cambia es **lo que el anillo tiene que ser**. Hoy es pletina de 14 fresada —cara vista de 20, rebaje de 6 donde asienta el acrílico coplanar, chaflán de 1,5 × 45° en las dos aristas, bolsillos cerrados para las tres planchas— porque **se ve** y porque **sujeta piel de acrílico**. Bajo la piel no se ve, y el acrílico de las mejillas ya no existe. Se queda con dos trabajos: cargar, y sujetar la trasera en su bolsillo. Para eso basta **pletina cortada** —láser o agua— con el bolsillo trasero y las roscas; sin chaflán, sin rebaje perimetral, sin cara vista. El hueso se abarata justo cuando la piel se encarece, y el taller de mecanizado del §6.1 del PLIEGO pasa a ser un corte.

Cómo se cuelga la piel del hueso no está dibujado (HUECO 1). Lo natural: la mejilla atornillada al anillo desde dentro por la cara del anillo que hoy es el rebaje, y la banda encajada entre mejillas.

---

## 7. Lo que esto reabre

### 7.1 D-V1: la fuente afuera, con este case

La v5 sacó la fuente por cuatro razones, y esta piel **toca una**:

| razón | con la piel |
|---|---|
| térmica: la caja no evacuaba | **se debilita, pero sigue**: con la fuente adentro da 18,5 K con el `C_D` de la puerta y **20,7 con el pesimista** — no pasa el peor caso por 0,7 K. Abriendo el tejido (separación 15 en vez de 13) pasaría; es una palanca, no un dato |
| el recinto de acero ocupa el 30 % del suelo | entera |
| la red de 230 V fuera de una caja de madera **y ahora de nylon** | entera, y más |
| el margen de U2 que se regala solo con el crudo a 15,5 | entera |
| un ladrillo de catálogo es lo práctico de fabricar | entera |

Así que el IEC del render **es una decisión que Samuel toma sabiendo el número**: si la fuente sale, ahí va un jack de DC; si se queda, este case la aguanta con el `C_D` de la puerta y **no** con el pesimista, salvo que la celosía abra más — y con un recinto de acero dentro de una piel de nylon, que es la clase de cosa que hay que decir en voz alta. Es D-P4, y no la decide este papel.

### 7.2 Tres papeles del case pierden su sujeto

- **30-08, el techo macizo con la salida por el alero**: el techo, la rendija, el labio de 18, los tacos, `guarda_rendija()` y la capilaridad — todo era de una chapa que ya no está. Mueren por desaparición del sujeto. El *criterio* sobrevive: el techo sigue macizo y sigue sin ranuras, porque la piel lo es.
- **28-08, la costilla de pletina**: el anillo sigue, el acabado no (§6).
- **29-08, las mejillas coplanares en el rebaje**: no hay mejillas de acrílico. `guarda_costado()`, el vano libre bajo el labio, `hol_costado` — sin sujeto.

### 7.3 El #289 muere, y las ranuras de la trasera cambian de razón

El encargo del #289 —22 244 mm² de venteo nuevo, o 7 610 con la v5— lo paga la celosía sola con 16 752 efectivos. **Se cierra por desaparición del sujeto** cuando esto se firme. Y las 46 ranuras de la trasera, que eran *la entrada*, valen 1,5 K: se quedan si Samuel las quiere como lenguaje —el concepto las conserva— y se van si no, sabiendo que cuestan eso. Es D-P5.

### 7.4 Los papeles del case, hacia atrás

La spec del chasis (`2026-08-15`) lleva 25 revisiones y este papel sería la 26. `case/README.md`, `PLIEGO.md` y `RFQ.md` cambian de fabricante (§9). Se enmiendan **cuando se firme**, cada uno con su issue e hito, como manda el CONTRIBUTING — y esta vez se ejecutan, porque el repo ya pagó dos veces una tabla de enmiendas sin ejecutar (#331).

---

## 8. Montaje y apertura — HUECO

Hoy la trasera entra con el anillo B, las tres planchas se montan una vez con el case, y el chasis del PSU entra al final por el frente. Con la piel en tres piezas (dos mejillas y la banda) ese orden se rediseña, y no está dibujado. Las preguntas, en el orden en que muerden:

1. ¿La banda es una pieza o dos mitades? Una pieza de 580 × 320 × 256 no entra en una MJF de serie (la HP 4200/5200 anda en ~380 × 284 × 380 — cifra de catálogo de memoria, sin hoja en el repo). **Dos mitades**, o resina de gran formato. Con D-P2 firmada esto deja de ser una opción y pasa a ser **la primera cota que hay que dibujar: dónde va la costura**. Una forma orgánica puede esconderla en un pliegue —el concepto tiene varios en el techo— y ahí es donde debería ir, no en el medio de una cara lisa.
2. ¿Por dónde se abre para llegar a la fila de abajo? Hoy por los paneles; sigue igual — la piel no los tapa.
3. ¿La mejilla se quita sin quitar la banda? Debería: es la pieza que se rompe.

---

## 9. Fabricación: cada pieza con quien le toca

| pieza | quién | proceso |
|---|---|---|
| **la piel** (dos mejillas, banda) | servicio de impresión (**D-P2, firmada**) | MJF PA12 W o resina blanca: la pieza impresa **es** el acabado, sin pintura ni fundición |
| **paneles de aluminio** | taller de mecanizado | como siempre se ha querido: tolerancia y canto |
| **anillos** | corte | láser o agua, pletina de 14, con bolsillo trasero y roscas. **Ya no fresados** |
| **trasera** | corte láser de PMMA | como hoy |
| **tabla** | el carpintero | como hoy |
| rieles, marco de ventana, tapa del valle | como hoy | |

Hace unas horas se preguntó qué era práctico para un luthier, y la respuesta fue el ladrillo. Esto es la respuesta contraria en la piel y la misma en todo lo demás — y es legítima: **una pieza de concepto para Superbooth se hace justo así**, una piel impresa sobre un hueso de corte y una base de madera.

### 9.1 Las piezas para imprimir

Samuel, la misma tarde: *«queremos tener las piezas listas para mandarlas a imprimir en 3D»*. `case/renders/imprimir_piel.py` las saca de `piel_organica.scad` y las deja en `case/print/piel/`, en tres pasos que son los que un servicio mira:

1. **El acabado de la referencia.** El extruido de OpenSCAD tiene todas las aristas a 90°; el despiece tiene los nervios como tubos blandos y el marco redondeado. Un **remallado por vóxeles** (0,7 mm) seguido de un **suavizado** convierte cada nervio de sección rectangular en sección casi redonda y funde las uniones. Es lo que hace que lea a hueso y no a recorte de tabla. Adelgaza un poco el nervio: se mide y se imprime.
2. **Malla cerrada**: cero aristas no-manifold en las tres piezas. **Tamaño** contra la bandeja MJF (380 × 284 × 380, catálogo). **Volumen** → gramos en PA12.
3. Tres STL: **el cachete** (una pieza, se imprime dos veces: el patrón se ve espejado de un lado al otro, como en el despiece) y **la cubierta en dos mitades**.

| pieza | mm | g en PA12 | cerrada | cabe |
|---|---|---|---|---|
| `cachete.stl` (×2) | 332 × 262 × 6 | ~195 | sí | sí |
| `banda_A.stl` | 332 × 262 × 296 | ~296 | sí | sí |
| `banda_B.stl` | 332 × 262 × 296 | ~297 | sí | sí |

**Lo que llevan y lo que no.** El cachete lleva **siete pasantes de Ø4,5 para M4** a 9 mm del canto, sobre la cara vista del anillo y dentro del marco macizo: dos abajo, uno en cada cara inclinada, uno en el techo, dos atrás — como los «orificios de montaje» del despiece. **El anillo necesita las siete roscas M4 en su cara exterior**: enmienda a `sam17_case.scad` cuando esto se firme. La cubierta va partida por el medio con un **solape de 12 mm a medio espesor** (A lleva la cara interior, B la exterior); la costura cae en el medio del techo y se mueve a un pliegue cuando la cubierta tenga su forma drapeada. **No llevan todavía**: los «puntos de enganche» cubierta-cachete del despiece (bossas con rosca en la cara interior del cachete), la forma drapeada de la cubierta, ni tolerancias de ajuste en el solape. Los tres son de la siguiente pasada, con los cachetes en la mano.

Los STL **no se versionan hasta la firma** (pesan ~10 MB cada uno y cambian con cada pasada de la celosía): los regenera el guion en segundos, y cuando D-P1 se firme el juego que se manda entra con su commit, como los DXF del láser.

---

## 10. Los renders

`case/renders/render_piel.py` reutiliza la escena de `render.py` entera y hace tres vistas: las dos de siempre y una **casi de lado** (`sam17-piel-lado.png`), que es la única desde la que se juzga la celosía.

Lo que enseñan: la piel blanca sobre el hueso, la celosía con el anillo asomando detrás en la orilla y el interior en el centro, los paneles de aluminio de las tres filas 7,5 dentro de la piel, la trasera en ámbar en su ventana, la tabla asomando 4 mm.

Lo que **no** enseñan, a propósito: la franja de conectores (§5, no modelada), la fuente (fuera), la sujeción de la piel al hueso (HUECO 1), y ningún control en los paneles — los paneles son placas lisas, como en `render.py`.

---

## 11. HUECOS

1. **Cómo se cuelga la piel del hueso.** No dibujado (§6, §8).
2. **La rigidez de la celosía.** Ramas de 2,6 a 7 mm en nylon de 6, huecos de 15 a 60 mm, puntas soldadas: sin calcular. Es lo que fija `W_PUNTA`, `W_MAX` y `BORDE` de verdad, y hoy son números de mirar. Y una rama sin soldar (queda una de 90) es un voladizo: o se suelda a mano o se poda.
3. **El `C_D` de un hueco entre ramas** en nylon de 6 mm: sin medir, como todo el `C_D`. Los huecos son alargados e irregulares, no ranuras.
4. **El polvo.** Dos mejillas abiertas al 45 % dejan entrar más que 46 ranuras. Ya se aceptó para la trasera; aquí es más, y se dice.
5. **El camino del aire por dentro**: el modelo es una chimenea y esto son dos. Orden de magnitud.
6. **La temperatura de la piel**: nylon a 45 + 17 = 62 °C como estructura secundaria (A). El PA12 de MJF tiene el HDT muy por encima de eso en la hoja de HP, pero **la cifra no está citada aquí a propósito**: va con página cuando la hoja esté en `docs/reference/datasheets/`, no de memoria. Y un HDT no es fluencia: lo que hay que mirar es el creep a 62 °C sostenidos con la piel colgada del hueso, que es carga baja y continua.
7. **La franja de conectores** de la trasera: sin modelar; enmienda al papel del 29-08.

---

## 12. Lo que Samuel decide

| | decisión | estado |
|---|---|---|
| **D-P1** | **la piel sustituye a techo, nariz, talón y las dos mejillas** (cinco pieles a una); la trasera se queda | pendiente |
| **D-P2** | material: **A**, piel impresa sobre el hueso de hoy; la pieza impresa es el acabado | **firmada 05-09** — *«todo el acabado se hace con impresión 3D»* |
| **D-P3** | la celosía abre sobre la ventana del anillo, interior a la vista (lo modelado) — o lleva el ámbar detrás como panel flotante con paso de aire arriba y abajo | pendiente |
| **D-P4** | la fuente: afuera (v5, D-V1) o adentro con esta piel — §7.1 | pendiente |
| **D-P5** | las 46 ranuras de la trasera: se quedan por lenguaje, o se van (valen 1,5 K) | pendiente |

Orden: mirar los renders → junta (Serrano sobre lo no verificado; Halberg sobre el nylon a 62 °C; Elke sobre la piel, el labio y cómo se cuelga) → firma → enmiendas de §7.4 en su orden, cada una con su issue.
