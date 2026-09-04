# La fila B es nuestra — el consumo de la fila de abajo como presupuesto, y el venteo que le corresponde — propuesta (v1, sin firmar)

**Fecha**: 2026-09-04 · **Estado**: **propuesta — pendiente de la junta y de la firma de Samuel (D-B1, D-B2 en §8)** ·
**Cierra**: nada. **Re-encarga**: #289 (el venteo, §3) y #169 (el bus board, §6) ·
**Mata por desaparición del sujeto**: nada. La fila B sigue existiendo; lo que muere es un **supuesto** sobre quién la llena, y un supuesto no es un issue ·
**Reabre**: fuente v4 §1, §6, §12 (fila 12) y §14 (D-F1 en sus rieles de rack); `hardware/01-power-supply/v4/calor_budget.py` (`PLACA_A` de rack, `P_CAJON_MAX`, la carga ultra); `case/cad/params.scad::potencia_disipada`; `case/clearance_budget.py::guarda_aire()`; `invitados_budget.py`; la spec del chasis §3.1 ·
**Origen**: Samuel, 2026-09-04: *«los otros modulos los vamos a fabricar nosotros tambien»*

---

## 0. Por qué existe este papel

Una palabra —**invitados**— pasó a significar dos cosas distintas entre dos
papeles, y el encargo más caro del case cuelga de la segunda.

| Cuándo | Dónde | Qué dice, textual |
|---|---|---|
| 2026-08-23 | acta #168, **E-4** | *«Los demás módulos **sí** son Eurorack intercambiables. La fila de abajo es rack de verdad, y pide bus board y reserva de invitados»* |
| 2026-08-23 | #169 (nace de E-4) | *«mixer de utilidad, delay analógico, **lo que Samuel quiera llevarse a otro instrumento**»*; reserva del orden de **230–300 mA por riel** |
| 2026-09-03 | fuente v4 §1 | la fila se dimensiona con **cuatro módulos ajenos del mercado** (Doepfer, Clouds, Morphagene, Disting EX): *«una fila entera de Disting EX es absurda, y cabe en placa»* → **3,8 A de placa, 95,6 W** en el cajón |
| 2026-09-04 | Samuel, en conversación | *«no habiamos quedado en que el sam17 es un instrumento de bajo consumo?»* y, sobre la fila de abajo, *«los otros modulos los vamos a fabricar nosotros tambien»* |

E-4 y #169 hablan de módulos **nuestros** en formato Eurorack para que sean
portables entre instrumentos KONDOR. La fuente v4 leyó «invitados» como
**módulos de otros**, con consumo desconocido, y compró el peor caso del
mercado. De esa lectura cuelgan: los 95,6 W de la fila (el 63 % de los
151,55 W del cajón), el listón de 3,8 A **declarado** en los rieles de rack,
y el encargo del #289 —22 446 mm² de venteo nuevo, una banda de ranuras en la
trasera y una rendija de 40 mm—, que el barrido del 04-09 enseñó que **ni la
trasera entera convertida en rejilla** puede pagar (36,8 K en el mejor caso).

El SAM17 sí es de bajo consumo: el instrumento analógico entero —16 voces,
filtros, VCAs, envolventes— son **8,0 W** (fuente v4 §6: 12 V × (340 + 327)
mA). Lo que lo subía a 151 no era el instrumento; era una promesa a
desconocidos que nadie hizo a propósito. Y es coherente con lo que Samuel
dijo el 27-08 al decidir el formato de la fila del valle: *«si materializo
este proyecto se va a vender como un solo instrumento completo, aunque por
dentro sea modular»*.

Este papel hace tres cosas: escribe lo que Samuel dijo donde el 03-09 se
escribió lo contrario (§1), pone cifra a lo que eso cambia en calor con los
guiones del repo (§2, §4), y re-encarga el venteo del #289 con lo que de
verdad hace falta (§3).

---

## 1. Las dos decisiones (propuestas)

| | Decisión | Consecuencia inmediata |
|---|---|---|
| **D-B1** | **La fila B es formato Eurorack para módulos KONDOR.** «Intercambiable» (E-4) significa *entre instrumentos KONDOR*. Un módulo ajeno **cabe mecánicamente** (3U, HP, peine de 16 sin llave, ±12 y +5 en el bus); **eléctricamente no se le promete nada**: el PTC por slot y riel del bus board (#169) se dimensiona al presupuesto de D-B2, y lo que se pase, dispara. El techo duro es una pieza, no una nota | fuente v4 §1: la fila de la tabla se renombra y sus tres rieles de rack cambian de columna (§6 de este papel); #169 cambia de sujeto; el censo de Disting/Clouds/Morphagene de `invitados_budget.py` pasa a **cota histórica**, no a requisito |
| **D-B2** | **Presupuesto de consumo de la fila B: 300 mA por riel de diseño y 500 mA por riel de techo duro**, en +12, −12 y +5 de rack, como **suma de los módulos KONDOR de la fila**, aseverado en guion igual que el del instrumento (`consumo_total_budget.py`) | `calor_budget.py`: los rieles de rack se declaran a **0,5 A** (`PLACA_A`) sobre los 3,8 de placa del módulo (`MODULO_A`, que no cambia); el cajón baja de 120,3 a **39,2 W** (§2); `params.scad::potencia_disipada` lo sigue por `guarda_potencia_vigente()`; el venteo del #289 se re-encarga (§3) |

**Por qué 300.** Es la reserva que E-4 y #169 tenían en mente (230–300
mA/riel) cuando la fila de abajo todavía se alimentaba del riel del
instrumento. No es un número nuevo: es el que estaba escrito antes de que la
v4 le diera rieles propios y el listón lo inflara.

**Por qué 500 de techo y no 700.** En conversación se dijo 700, que es lo que
la rendija de 20 mm sostiene con un modelo lineal y **sin la carga ultra**.
Con los guiones del repo (§2) la carga ultra son 8,0 W que `calor_budget.py`
no cuenta en el cajón, y con ellos 700 mA queda en **19,8 K** contra un techo
de 20 (§3, tabla): eso no es margen, es el filo. A 500 mA son **18,6 K**. Y
500 ya es **1,7 veces** el diseño: un módulo nuestro que se pase del
presupuesto tiene sitio para pasarse antes de que salte la puerta.

**Lo que D-B2 le hace a D-F1.** D-F1 (firmada 03-09) declaró el listón «como
corriente de placa» y en los rieles de rack puso 3,8 / 2,5 / 4,0 A. Ese número
mezclaba dos cosas que `invitados_budget.py` ya separa en cuatro columnas:
**lo que el módulo puede dar** (3,8 A, hoja p. 2: sigue), **lo que el
instrumento declara** (pasa a 0,5 A: D-B2), **lo que el calor deja sostener**
(≈ 1,9–2,0 A según modelo, §4: es *capacidad*, no promesa) y **lo que la fila
pide** (los módulos KONDOR, que hoy no existen: HUECO hasta el primero). La
IRM-45 se queda: sobrada no cuesta calor, y achicarla sería otro papel.

---

## 2. Lo que cambia en calor

Con las funciones del propio `calor_budget.py` (`p_cajon_w` + `p_recinto_w`
con los tres rieles de rack a la misma corriente; corrida del 04-09), **más
8,0 W de carga ultra** que ese guion no cuenta y que este papel añade (§7.1):

| Fila B a … | Fila | Digital (peor caso, #256) | Recinto de la fuente | Carga ultra | **Total en el cajón** |
|---|---|---|---|---|---|
| 0 mA/riel (solo el SAM17) | 0,00 | 24,7 | 16,50 | 8,00 | **49,20 W** |
| **300 mA/riel (diseño)** | 8,70 | 24,7 | 17,82 | 8,00 | **59,23 W** |
| **500 mA/riel (techo duro)** | 14,50 | 24,7 | 18,71 | 8,00 | **65,91 W** |
| 700 mA/riel | 20,30 | 24,7 | 19,59 | 8,00 | 72,60 W |
| 3,8 A de placa (hoy, sin la ultra) | 95,60 | 24,7 | 31,25 | — | 151,55 W |

De 151,55 a **59,23 W** en el punto de diseño. Y la mitad de lo que queda son
los 24,7 W del digital, que salen de una tabla de ST a 125 °C que no publica
el valor a 85 (#256); al típico serían ~7 W. **No se cuenta**: es una palanca,
no un dato.

---

## 3. El venteo que corresponde — el re-encargo del #289

Barrido del 04-09 con `clearance_budget._tiro()` —el modelo de
`guarda_aire()`, con las tres fuentes de área sustituidas— sobre las potencias
de §2. Salto del case en K sobre ambiente; techo 20; `C_D = 0,65`.

| Geometría | Entrada mm² | Efectiva mm² | Tiro mm | Evacúa a 20 K | 0 mA | **300** | **500** | 700 | 1 A |
|---|---|---|---|---|---|---|---|---|---|
| Hoy | 7 065 | 3 299 | 105 | 19,4 W | 37,2 | 42,1 | 45,2 | 48,2 | 52,5 |
| Entrada de hoy (trasera) + rendija de 20 | 7 065 | 5 669 | 158 | 40,9 W | 22,6 | 25,6 | 27,5 | 29,3 | 32,0 |
| Suelo + patas 20 + rendija de 15 | 27 019 | 7 402 | 196 | 59,5 W | 17,6 | 19,9 | 21,4 | 22,8 | 24,9 |
| **Suelo + patas 20 + rendija de 20** | **27 019** | **8 961** | **204** | **73,5 W** | **15,3** | **17,3** | **18,6** | 19,8 | 21,6 |
| Suelo + patas 20 + rendija de 25 | 27 019 | 10 426 | 210 | 86,6 W | 13,7 | 15,5 | 16,7 | 17,8 | 19,4 |
| Suelo con 20 000 de ranura (no 40 000) + rendija de 20 | 17 555 | 8 355 | 204 | 68,5 W | 16,0 | 18,2 | 19,5 | 20,8 | 22,7 |
| Suelo + patas **15** + rendija de 20 | 22 650 | 8 760 | 204 | 71,8 W | 15,5 | 17,6 | 18,9 | 20,1 | 22,0 |

Tres cosas que la tabla dice solas:

1. **Ni el SAM17 solo pasa en la caja de hoy** (37,2 K). Algo hay que ventilar
   sea cual sea la fila.
2. **La entrada por el suelo es la palanca grande, no la rendija.** La misma
   rendija de 20 con la entrada de hoy da 25,6 K; con el suelo, 17,3. Es el
   tiro: de 105 a 204 mm.
3. **Las patas importan hasta 20 y no más allá** (15 → 17,6; 20 → 17,3; 25 →
   17,2). Y la mitad del área de ranuras en la tabla cuesta ~1 K.

### 3.1 Lo que se dibuja

**(a) La entrada: ranuras en la tabla de madera, y patas de 20.** El aire
entra por debajo del case —por el hueco entre la tabla y la mesa— y sube por
ranuras en la tabla (`suelo: TABLA DE MADERA MACIZA t=18`, esqueleto-aluminio
§9.1). El hueco perimetral (20 mm × 1 832 mm de perímetro = 36 600 mm²) va
**en serie** con las ranuras; con 40 000 mm² brutos de ranura da 27 019 mm²
efectivos de entrada, a y = 0. Las ranuras van **fuera de la huella del
recinto de la fuente** (la franja de 230 V no respira: `check_red_chasis.py`)
y fuera de los apoyos de los largueros.

Esto **revierte la rev. 13 del case (21-08)**, que sacó la entrada del suelo
porque *«el acrílico naranja es traslúcido y el campo de ranuras se veía por
el canto inferior»*. Esa razón murió el 26-08: el suelo ya no es el vuelo de
la bandeja de acrílico, es una tabla de madera maciza, y la madera no se
transparenta.

**(b) La salida: la rendija del alero pasa de 4,0 a 20 mm de luz nominal**
(16 comprimida, con `compresion_taco`). Las dos ondas de la trasera **siguen
contando como salida** (sin ellas, +2 K). Cómo se hacen los 16 mm de más:
**crece el vuelo del techo, la trasera no retrocede** — el interior es para
los módulos y el cableado, y retroceder la trasera le quita 16 mm de fondo a
la fila de arriba. El labio del techo sigue tapando el canto de
la trasera; `guarda_rendija()` **mejora**, porque la subida capilar va con
1/d: 0,9 mm a 16 de luz contra 4,7 hoy. Los tacos dejan de ser láminas y
pasan a ser piezas de 20 (o una tira): *el taco ES la luz* sigue valiendo.

**(c) Lo que no se toca.** La trasera: ni banda de ranuras arriba, ni más
columnas abajo; el PMMA de 8, las 46 ranuras, las dos ondas y el relieve
KONDOR quedan como están. El techo macizo (30-08: *«esa parte es sensible a
que le entren liquidos»*). La franja de 230 V, cerrada. Sin filtro: se
comería el `C_D`, que ya es el número que más manda y el único sin medir; el
polvo es el precio declarado de D-F3 = A y lo mide el ensayo térmico de la
primera unidad (paso 7 del bring-up). La pared exterior **no entra en la
puerta**.

### 3.2 El resultado, por los dos lados

Geometría recomendada (suelo 40 000 + patas 20 + rendija 20):

| | 300 mA/riel | 500 mA/riel |
|---|---|---|
| Salto, `C_D = 0,65` (la puerta) | **17,3 K** | **18,6 K** |
| Salto, `C_D = 0,55` (aviso) | 19,4 K | 20,8 K |
| Contando la pared exterior (`U = 3`, SUPUESTO; aviso, no veredicto) | 11,7 K (se lleva 26,4 W) | 12,8 K (28,3 W) |

En el punto de diseño el case pasa **incluso con el `C_D` pesimista**. En el
techo duro pasa con el `C_D` de la puerta y no con el pesimista: por eso el
techo es 500 y no 700, y por eso el paso 7 mide.

### 3.3 Lo que el dibujo tiene que resolver, y con qué puerta

- **El área de ranuras de la tabla es un parámetro nuevo** (`tabla_ranuras_mm2`
  o el censo de ranuras que el `.scad` corte) **con puerta por los dos lados**
  —un aserto con solo cota inferior no cuenta; ya pasó con el radio y con el
  alivio—: cota inferior por el tiro, superior por lo que la tabla aguanta
  como suelo con 21 % de material quitado (40 000 de 192 700 mm²), que hoy
  nadie ha calculado.
- **`alto_pie` entra en `guarda_aire()`.** El comentario de `params.scad`
  (*«La altura sale gratis […] alto_pie no entra en ninguna derivacion»*) deja
  de ser verdad: el hueco perimetral va en serie con la entrada. La patica con
  hoja (flecha 0,25 mm) es de 10 de alto: o hay una de 20 con la misma curva
  carga-deformación, o va un suplemento rígido bajo la de 10. Es requisito de
  compra, como ya lo era la flecha.
- **`C_D` de una ranura en madera de 18 mm** (L/D ≈ 5) no es el de chapa ni
  el de tubo. Sin medir, como todo el `C_D`. Se publica, no se asevera.
- **Rendija de 20 o de 25, y cuánto vuelo de techo**: se decide mirando el
  render, no aquí. Las dos son verdes; la de 25 compra 1,9 K en el techo
  duro.
- La spec del case (**§3.1, §3.2, §3.3 y §4 de la spec del chasis**, y el
  papel del case) recibe estas cotas cuando Samuel firme.

---

## 4. El recinto de la fuente: la etapa que queda apretada

Al bajar el cajón, lo que manda pasa a ser el **recinto de acero de la
fuente**, y conviene decirlo aquí aunque sea papel de la fuente. Tres
temperaturas en serie: sala de diseño **45 °C** (spec del chasis §3.1) + el
aire del cajón + el aire del recinto sobre el del cajón. El recinto disipa
**16,5 W constantes** (cascada, `PS6` al digital, NTC y choke) más lo que
escale con la fila, por 0,1453 m² de chapa a 9 W/m²K y su chimenea propia de
83 mm. Y la curva de la IRM-45 **termina a 70 °C**.

Con la etapa del recinto de `calor_budget.py` (sus constantes, su
`sostenido_a()` leyendo la curva) sobre el salto del case de §3:

| Fila B a … | Case | Recinto **cerrado** → aire | Venteo **propio** del recinto para 70,0 °C | Con 10 000 mm² propios → aire; rack sostenido |
|---|---|---|---|---|
| 0 mA/riel | +15,3 K | 72,9 °C (fuera de curva) | 2 262 mm² | 66,4 °C; 2,24 / 2,24 / 4,00 A |
| **300 mA/riel** | **+17,3 K** | **76,0 °C** (fuera de curva) | **6 526 mm²** | **68,8 °C; 2,01 / 2,01 / 4,00 A** |
| 500 mA/riel | +18,6 K | 77,9 °C (fuera de curva) | 11 398 mm² | 70,4 °C; 1,88 / 1,88 / 3,95 A |

Dos lecturas:

- **D-F3 = A sigue en pie y su parte del recinto no es opcional.** Sin
  abertura propia el recinto está fuera de curva **hasta con la fila a cero**.
  Con ~6 500 mm² propios a 300 mA los módulos quedan a 1 K del fin de su
  curva a 45 °C de sala. Es `calor_budget.py` (`AREA_VENTEO_MIN_MM2`,
  re-corrido con `PLACA_A` de D-B2) quien fija ese número, no este papel:
  aquí es orden de magnitud.
- **El listón sostenido sobrevive como capacidad.** Con 10 000 mm² propios y
  la fila a 300 mA los rieles de rack sostienen ~2,0 / 2,0 / 4,0 A — el nivel
  PSU3 que la fuente v4 re-firmó el 03-09 — porque lo que deratea los IRM es
  el aire del recinto, y ese aire lo gobiernan ahora sus propias pérdidas y el
  cajón, no la fila. Lo que cambia es **qué se promete**: 300 de diseño y 500
  de techo (D-B2). Si alguien sacara 2 A de verdad, el cajón subiría ~49 W
  (58 W de fila contra 8,7) y el propio calor lo recortaría — el PTC por slot
  está para que no llegue a probarlo.

---

## 5. Lo que NO cambia

| | Sigue | Por qué |
|---|---|---|
| **D-F1**, la fuente física | seis IRM, `PS3`/`PS4` = IRM-45-12 con 3,8 A de placa | capacidad del módulo, no promesa; sobrada no cuesta calor. D-B2 enmienda la **columna declarada** de los rieles de rack, no la pieza |
| **D-F3 = A** | ventilar recinto y cajón, sin ventilador | §4: el recinto lo necesita con la fila a cero. Lo que cambia es cuánto (§3, §4) |
| **D-F4, D-F6** | secuenciador ±12 de rack, crowbar de rack | 16,2 V sobre una fila de módulos **nuestros** es tan malo como sobre ajenos; ±12 con uno fijo y otro ciclando, igual |
| **D-F7** | `PS5` = IRM-45-5 | no depende de la fila |
| Techo del case | 20 K sobre ambiente (`tuning_budget.py`, PR #311) | es la deriva de afinación, no la fila |
| Techo macizo, trasera capturada, KONDOR, las dos ondas | como el 30-08 | §3.1(c) |
| `C_D`, `U` de la pared, los 24,7 W del digital | supuestos que **no entran en la puerta** | se miden en el paso 7 (`C_D`, `U`) y en #256 (digital) |

---

## 6. Enmiendas a otros papeles

Se ejecutan **cuando D-B1 y D-B2 estén firmadas**, en el orden de la tabla,
cada una con su issue en el hito que le toca (CONTRIBUTING: todo issue lleva
hito). Una tabla de enmiendas que nadie ejecuta deja dos arquitecturas vivas
en `main`; este repo ya lo pagó una vez, y por eso cada fila lleva quién.

| # | Dónde | Tipo | Qué | Quién |
|---|---|---|---|---|
| 1 | fuente v4 §1 (tabla del listón) | Rewrite | las tres filas «invitados» pasan a **«fila B (KONDOR)»** con las cuatro columnas: placa del módulo 3,8 / 3,8 / 8,0 · **declarado 0,5 / 0,5 / 0,5** (D-B2) · sostenido según modelo ≈ 2,0 / 2,0 / 4,0 (§4, capacidad) · censo = los módulos KONDOR de la fila (HUECO). El bloque «Por qué 3,8 A de placa y no los 2 A de la PSU3» se **tacha, no se borra**: una propuesta que borra sus razones caídas se lee mejor de lo que es | issue nuevo, hito 1 |
| 2 | fuente v4 §6 | Update | «la fila de invitados a placa disipa 95,6 W» → 8,7 W a 300 mA y 14,5 al techo; la tabla de calor del cajón con la carga ultra (8,0 W) que le faltaba; el «encargo» de 25 745 mm² totales se sustituye por §3 de este papel | mismo issue que 1 |
| 3 | fuente v4 §12 fila 12, §14 | Update | fila 12 («el listón compró un máximo que no existe») se cierra con este papel; en §14 nota bajo D-F1: «rieles de rack: declarado según D-B2 (papel fila B propia)» | mismo issue que 1 |
| 4 | `calor_budget.py` | Patch + Expand | `PLACA_A["rack+12"/"rack-12"/"rack+5"]` → **0,5** (techo duro D-B2); `P_CAJON_MAX` se deriva solo; **nueva constante de carga ultra** derivada de `consumo_total_budget.py` (12 V × los dos rieles a censo), no transcrita; `AREA_VENTEO_MIN_MM2` se re-corre y pasa a ser **el venteo propio del recinto** (§4); `test_calor_budget.py` sigue atando `A_EF_BASE_MM2` a `params.scad` (cambia con el suelo) | issue nuevo, hito 1; **con TDD**: el contrato que hoy ata el cajón a los 120,3 W del papel (`p_cajon_w(PLACA_A)`, docstring) se pone rojo a propósito antes de tocar la constante |
| 5 | `case/cad/params.scad`, `clearance_budget.py::guarda_aire()` | Expand | `potencia_disipada` sigue a `calor_budget.py` (`guarda_potencia_vigente()` lo cruza: rojo hasta copiar); entrada por el suelo (`_rejilla_suelo()` con las ranuras de la tabla **en serie** con `alto_pie × perímetro`); `aire_labios` 4 → 20; cada parámetro nuevo con puerta por los dos lados y su canario; la rejilla de la trasera **deja de ser entrada** y se queda como está (si el modelo la cuenta como entrada secundaria, que lo diga) | #289 re-encargado (§3), hito 6 |
| 6 | `invitados_budget.py` | Rewrite del sujeto | de «cuatro corrientes que se llamaban igual» sobre un censo del mercado, a **el presupuesto de la fila B**: `PRESUPUESTO_FILA_B_MA = 300`, `TECHO_FILA_B_MA = 500`, aseverados contra la suma de los módulos KONDOR de la fila (HUECO hasta el primero); el censo de Disting/Clouds/Morphagene se conserva como cota histórica tachada. `consumo_total_budget.py` lo sigue nombrando por su nombre: no se renombra | issue nuevo, hito 5 |
| 7 | #169 | Update | título y cuerpo: «un módulo ajeno espera el peine» → módulos KONDOR; el PTC por slot y riel se dimensiona al presupuesto de D-B2 repartido por slot (valor: #169); la reserva «230–300 mA a escribir» **ya está escrita**: es D-B2 | comentario en #169, hito 5 |
| 8 | #289 | Update | el encargo pasa de 22 446 mm² nuevos + banda + rendija de 40 a **§3 de este papel**; los criterios de cierre se reescriben: suelo, patas, rendija, `guarda_aire()` verde con 59,23 W a 300 mA | comentario en #289, hito 6 |
| 9 | spec del chasis §3.1 | Update | los 151,55 W y el «venteo mínimo 22 200» → §2 y §4 de este papel; la abertura propia del recinto como requisito | mismo issue que 1 |
| 10 | `hardware/01-power-supply/v4/README.md`, `docs/modules/01-power-supply.md` | Sync | «una fila Eurorack de invitados» → «la fila B, módulos KONDOR en formato Eurorack» | mismo issue que 1 |

---

## 7. Hallazgos y huecos

1. **`calor_budget.py` no cuenta la carga ultra en el cajón.** `P_CAJON_MAX`
   suma rieles de rack × tensión + digital; los ±12 V ultra que alimentan la
   Voz (12 V × (340 + 327) mA = **8,0 W**, fuente v4 §6) se disipan en la Voz,
   dentro del cajón, y no están. Son el 14 % del cajón de §2. Enmienda 4.
2. **A 45 °C de sala, el recinto es la etapa apretada.** Con la fila a cero y
   el recinto cerrado, los IRM están fuera de curva (72,9 °C). Con ~6 500 mm²
   propios a 300 mA quedan a 1 K del fin de la curva. Lo que lo relaja sin
   chapa: los 4,88 W de `PS6` al digital de peor caso (#256) y los 3,7 W de
   NTC + choke. HUECO de la fuente, no de este papel.
3. **`alto_pie` deja de estar fuera de toda derivación** (§3.3). Un parámetro
   que un comentario declara inerte y una puerta nueva usa es una mentira con
   fecha: el comentario se reescribe en la misma PR que la puerta.
4. **`C_D` de ranura en madera** sin medir; **`U` de la pared** sin medir;
   los dos van al paso 7 del bring-up con la primera unidad.
5. **El +5 V de rack a 300 mA es conservador**: un módulo analógico nuestro
   rara vez lo usa. Se deja así; sobra en la dirección segura.
6. **Los 40 000 mm² de ranura en la tabla son el 21 % del suelo.** Si el dibujo
   no los encuentra fuera de la huella del recinto y de los largueros, 20 000
   dan 18,2 K a 300 mA (§3, tabla): sigue verde. El número lo fija el dibujo,
   con su puerta.
7. **Lo que el 04-09 se dijo en conversación y este papel corrige**: el techo
   duro pasa de 700 a **500 mA** (§1, por la carga ultra), y la geometría
   recomendada no cambia.

---

## 8. Lo que Samuel decide

| | Decisión | Estado |
|---|---|---|
| **D-B1** | la fila B es formato Eurorack para módulos KONDOR; a un módulo ajeno no se le promete corriente | **pendiente** |
| **D-B2** | 300 mA/riel de diseño, 500 mA/riel de techo duro, aseverados en guion | **pendiente** |
| **D-B3** | rendija del alero: **20** o **25** mm; y el vuelo del techo crece (la trasera no retrocede) | **se decide mirando el render** (§3.3) |

Orden: junta (Serrano sobre las premisas y lo no verificado; Elke sobre el
suelo, las patas y el alero) → firma → enmiendas de §6 en su orden.
