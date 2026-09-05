# La piel orgánica: cinco pieles a una, y las mejillas que respiran

**Fecha**: 2026-09-05 · **Estado**: **propuesta — sin firmar** (D-P1 a D-P5 en §12) ·
**Sucede a**: nada; **se apoya en** `2026-08-28-costilla-pletina` (el anillo), `2026-08-29-trasera-capturada-talon-nariz` (la trasera, que se queda), `2026-08-30-techo-macizo-chapas-empotradas` (el techo, que se va), `2026-08-31-case-tanda-b` (las tres filas, que no se tocan) y `2026-09-05-fuente-v5-ladrillo` (la fuente afuera, que este papel reabre en §7.1) ·
**No toca**: la silueta, los ángulos, las tres filas, los Z-Rails, el marco de la ventana, los paneles rehundidos, la tabla, el ámbar ·
**Referencia visual**: tres renders de concepto generados por Samuel el 05-09, en `docs/images/case-piel-organica/`. **Mandan sobre lenguaje, no sobre cotas** — la misma regla que el board del 16-08 y la foto del 26-08. Samuel, sobre ellos: *«lo que está en los paneles es conceptual pero se entiende que va con el diseño que estamos haciendo, lo del valle seguimos trabajándolo como veníamos [...] son módulos de la fila B»* ·
**Modelo**: `case/cad/piel_organica.scad` (al lado de `sam17_case.scad`, sin tocarlo), `case/cad/celosia.py` → `celosia_celdas.scad`, `case/renders/render_piel.py` → `sam17-piel*.png`.

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

### 3.2 Material: la única pregunta de estructura (D-P2)

**A. La piel es piel.** Nylon impreso (MJF PA12, o resina) sobre los anillos de hoy, que se esconden. La estructura no cambia: los anillos cargan, el marco de la ventana ata los rieles, la piel se cuelga de ellos. Riesgo cero en lo que ya está calculado. Los paneles de aluminio hacen de disipador (§4.4).

**B. La piel es aluminio fundido** y hace de hueso y de disipador a la vez. Más pesada, molde, más cara — y la versión de serie si algún día hay serie.

**Recomendación: A**, para la pieza de concepto y como base. B se decide con una unidad vendida, no antes. Y con A hay una cosa que no se puede olvidar: **a 45 °C de sala más 14–17 K dentro, un nylon impreso aguanta como piel y no como estructura**. Por eso A exige que el hueso siga.

---

## 4. La celosía

### 4.1 Por qué por guion y no a mano

Del dibujo orgánico importan tres números —cuánto abre, cuánto nervio le queda, cuánto borde macizo la enmarca— y los tres tienen que ser **parámetros**, porque el primero lo lee el modelo térmico y los otros dos los leerá la rigidez. Un dibujo no tiene parámetros. `celosia.py` genera celdas de Voronoi sobre el perfil del case (`clearance_budget._vertices()`, la misma fórmula que `pts_perfil()`), las estira en vertical para que salgan más altas que anchas como en el concepto, y las escribe en `celosia_celdas.scad` con su área medida. Determinista: misma semilla, misma celosía.

| parámetro | valor | qué es |
|---|---|---|
| `CELDA` | 22 mm | paso medio entre semillas |
| `ANISO` | 1,8 | estiramiento vertical |
| `NERVIO` | 3,5 mm | ancho del nervio entre celdas |
| `REDONDEO` | 3,0 mm | radio de las esquinas de cada celda |
| `BORDE` | 12 mm | marco macizo alrededor de la celosía, desde el perfil |
| `SEMILLA` | 17 | |

Salen **61 celdas** por mejilla. (El primer render del 05-09 salió con 26 / 1,5 / 4,0 y 53 celdas: grandes respecto al case. Se afinó mirándolo, que es como se decide esto; el modelo térmico se movió 0,1 K.)

### 4.2 Dos áreas, y por qué no son la misma

La celosía abre desde 12 mm del perfil hacia dentro: eso es **lo que se ve**. Pero detrás de la mejilla está el anillo (20 de cara) y el marco de la ventana (hasta `marco_fondo` = 26 del perfil), y las celdas que caen sobre ese metal no respiran: enseñan aluminio. **Lo que respira es lo abierto sobre la ventana del anillo.**

| por mejilla | mm² | del perfil (52 658) |
|---|---|---|
| región de la celosía (a ≥ 12 del perfil) | 40 693 | 77 % |
| **abierto, lo que se ve** (nervio descontado) | **30 933** | **58,7 %** |
| **abierto sobre la ventana, lo que respira** (a ≥ 26) | **22 021** | **41,8 %** |

Medido por muestreo (200 000 puntos), con las celdas encogidas `NERVIO/2`. Dos cosas que el número no lleva y se declaran: el redondeo de esquinas del `.scad` quita algo más (< 2 %), y `marco_fondo_trasera` es 30 y no 26 — se usa 26 en todo el contorno, 4 mm optimista en el tramo trasero.

Visualmente, el anillo detrás de las celdas del borde **no es un defecto**: es la opción A hecha visible — celosía blanca sobre aluminio en la orilla, sobre el ámbar del interior en el centro.

### 4.3 Lo que le pasa al calor

Con `clearance_budget._tiro()` —el modelo de `guarda_aire()`— y las dos mejillas como chimenea: la mitad baja de cada una entra, la mitad alta sale, centroides a un cuarto y tres cuartos del alto; más la rejilla baja de la trasera, que el concepto conserva. Techo, 20 K sobre una sala de 45 °C. `C_D` = 0,65 el de la puerta, 0,55 el pesimista.

| escenario | W | salto | pesimista | sin la rejilla trasera |
|---|---|---|---|---|
| **v5 declarada, fuente afuera** | 64,2 | **13,8 K** | **15,4 K** | 15,1 K |
| v5 a censo | 35,1 | 9,2 K | 10,3 K | 10,1 K |
| **fuente ADENTRO** (v5 + los 25,02 que se irían) | 89,2 | **17,2 K** | **19,2 K** | 18,8 K |
| *hoy, para comparar* | 64,2 | 45,6 K | 51,0 K | — |

Área efectiva **18 653 mm²** (hoy 3 299), tiro **119 mm** (hoy 105).

Tres lecturas:

1. **Es la primera geometría que pasa con el `C_D` pesimista.** Ni la trasera agrandada, ni el suelo ranurado, ni la rendija ancha lo conseguían (v5 §6): la mejor daba 21,0 K. Ésta da 15,4, y con el suelo y el techo macizos.
2. **La rejilla baja de la trasera vale 0,3 K.** Térmicamente sobra. Se queda o se va por identidad (§7.3), no por calor.
3. **Con la fuente adentro también pasa**, 19,2 K pesimista contra 20. Por un pelo, y eso reabre D-V1 — ver §7.1.

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
| térmica: la caja no evacuaba | **se debilita**: con la fuente adentro da 17,2 K, 19,2 pesimista. Pasa por un pelo |
| el recinto de acero ocupa el 30 % del suelo | entera |
| la red de 230 V fuera de una caja de madera **y ahora de nylon** | entera, y más |
| el margen de U2 que se regala solo con el crudo a 15,5 | entera |
| un ladrillo de catálogo es lo práctico de fabricar | entera |

Así que el IEC del render **es una decisión que Samuel toma sabiendo el número**: si la fuente sale, ahí va un jack de DC; si se queda, este case la aguanta — a un kelvin del techo en el peor caso, y con un recinto de acero dentro de una piel de nylon, que es la clase de cosa que hay que decir en voz alta. Es D-P4, y no la decide este papel.

### 7.2 Tres papeles del case pierden su sujeto

- **30-08, el techo macizo con la salida por el alero**: el techo, la rendija, el labio de 18, los tacos, `guarda_rendija()` y la capilaridad — todo era de una chapa que ya no está. Mueren por desaparición del sujeto. El *criterio* sobrevive: el techo sigue macizo y sigue sin ranuras, porque la piel lo es.
- **28-08, la costilla de pletina**: el anillo sigue, el acabado no (§6).
- **29-08, las mejillas coplanares en el rebaje**: no hay mejillas de acrílico. `guarda_costado()`, el vano libre bajo el labio, `hol_costado` — sin sujeto.

### 7.3 El #289 muere, y las ranuras de la trasera cambian de razón

El encargo del #289 —22 244 mm² de venteo nuevo, o 7 610 con la v5— lo paga la celosía sola con 18 653 efectivos. **Se cierra por desaparición del sujeto** cuando esto se firme. Y las 46 ranuras de la trasera, que eran *la entrada*, valen 0,3 K: se quedan si Samuel las quiere como lenguaje —el concepto las conserva— y se van si no. Es D-P5.

### 7.4 Los papeles del case, hacia atrás

La spec del chasis (`2026-08-15`) lleva 25 revisiones y este papel sería la 26. `case/README.md`, `PLIEGO.md` y `RFQ.md` cambian de fabricante (§9). Se enmiendan **cuando se firme**, cada uno con su issue e hito, como manda el CONTRIBUTING — y esta vez se ejecutan, porque el repo ya pagó dos veces una tabla de enmiendas sin ejecutar (#331).

---

## 8. Montaje y apertura — HUECO

Hoy la trasera entra con el anillo B, las tres planchas se montan una vez con el case, y el chasis del PSU entra al final por el frente. Con la piel en tres piezas (dos mejillas y la banda) ese orden se rediseña, y no está dibujado. Las preguntas, en el orden en que muerden:

1. ¿La banda es una pieza o dos mitades? Una pieza de 580 × 320 × 256 no entra en una MJF de serie (la HP 4200/5200 anda en ~380 × 284 × 380 — cifra de catálogo de memoria, sin hoja en el repo). **Dos mitades**, o resina.
2. ¿Por dónde se abre para llegar a la fila de abajo? Hoy por los paneles; sigue igual — la piel no los tapa.
3. ¿La mejilla se quita sin quitar la banda? Debería: es la pieza que se rompe.

---

## 9. Fabricación: cada pieza con quien le toca

| pieza | quién | proceso |
|---|---|---|
| **la piel** (dos mejillas, banda) | servicio de impresión | MJF PA12 (natural/teñido; el blanco del concepto pide PA12 W o resina y pintura) — o fundición (B) |
| **paneles de aluminio** | taller de mecanizado | como siempre se ha querido: tolerancia y canto |
| **anillos** | corte | láser o agua, pletina de 14, con bolsillo trasero y roscas. **Ya no fresados** |
| **trasera** | corte láser de PMMA | como hoy |
| **tabla** | el carpintero | como hoy |
| rieles, marco de ventana, tapa del valle | como hoy | |

Hace unas horas se preguntó qué era práctico para un luthier, y la respuesta fue el ladrillo. Esto es la respuesta contraria en la piel y la misma en todo lo demás — y es legítima: **una pieza de concepto para Superbooth se hace justo así**, una piel impresa sobre un hueso de corte y una base de madera.

---

## 10. Los renders

`case/renders/render_piel.py` reutiliza la escena de `render.py` entera y hace tres vistas: las dos de siempre y una **casi de lado** (`sam17-piel-lado.png`), que es la única desde la que se juzga la celosía.

Lo que enseñan: la piel blanca sobre el hueso, la celosía con el anillo asomando detrás en la orilla y el interior en el centro, los paneles de aluminio de las tres filas 7,5 dentro de la piel, la trasera en ámbar en su ventana, la tabla asomando 4 mm.

Lo que **no** enseñan, a propósito: la franja de conectores (§5, no modelada), la fuente (fuera), la sujeción de la piel al hueso (HUECO 1), y ningún control en los paneles — los paneles son placas lisas, como en `render.py`.

---

## 11. HUECOS

1. **Cómo se cuelga la piel del hueso.** No dibujado (§6, §8).
2. **La rigidez de la celosía.** Nervios de 4 en nylon de 6, celdas de ~25 × 40: sin calcular. Es lo que fija `NERVIO` y `BORDE` de verdad, y hoy son números de mirar.
3. **El `C_D` de una celda de celosía** en nylon de 6 mm: sin medir, como todo el `C_D`.
4. **El polvo.** Dos mejillas abiertas al 42 % dejan entrar más que 46 ranuras. Ya se aceptó para la trasera; aquí es más, y se dice.
5. **El camino del aire por dentro**: el modelo es una chimenea y esto son dos. Orden de magnitud.
6. **La temperatura de la piel**: nylon a 45 + 17 = 62 °C como estructura secundaria (A). El PA12 de MJF tiene el HDT muy por encima de eso en la hoja de HP, pero **la cifra no está citada aquí a propósito**: va con página cuando la hoja esté en `docs/reference/datasheets/`, no de memoria. Y un HDT no es fluencia: lo que hay que mirar es el creep a 62 °C sostenidos con la piel colgada del hueso, que es carga baja y continua.
7. **La franja de conectores** de la trasera: sin modelar; enmienda al papel del 29-08.

---

## 12. Lo que Samuel decide

| | decisión | estado |
|---|---|---|
| **D-P1** | **la piel sustituye a techo, nariz, talón y las dos mejillas** (cinco pieles a una); la trasera se queda | pendiente |
| **D-P2** | material: **A**, piel impresa sobre el hueso de hoy (recomendada) — o B, fundida y portante | pendiente |
| **D-P3** | la celosía abre sobre la ventana del anillo, interior a la vista (lo modelado) — o lleva el ámbar detrás como panel flotante con paso de aire arriba y abajo | pendiente |
| **D-P4** | la fuente: afuera (v5, D-V1) o adentro con esta piel — §7.1 | pendiente |
| **D-P5** | las 46 ranuras de la trasera: se quedan por lenguaje, o se van (valen 0,3 K) | pendiente |

Orden: mirar los renders → junta (Serrano sobre lo no verificado; Halberg sobre el nylon a 62 °C; Elke sobre la piel, el labio y cómo se cuelga) → firma → enmiendas de §7.4 en su orden, cada una con su issue.
