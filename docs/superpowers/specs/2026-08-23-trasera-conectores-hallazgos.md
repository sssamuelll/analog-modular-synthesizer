# La trasera deja de ser solo aire — hallazgos antes de dibujar nada

Origen: [#167](https://github.com/sssamuelll/sam17/issues/167) (decisión de
Samuel del 2026-08-23) y [#130](https://github.com/sssamuelll/sam17/issues/130),
que son el mismo problema: agujeros en la misma plancha.

**Qué es este documento y qué no.** Es lo que encontré leyendo el modelo y los
specs que ya existen, antes de tocar una línea del `.scad`. No propone cotas de
recorte: no se pueden proponer todavía, y §4 explica por qué. Lo que sí trae son
**tres decisiones que no cuestan dinero** y que hoy están tomadas por omisión.

El #167 pedía que el [#165](https://github.com/sssamuelll/sam17/pull/165) fuera
primero. Ya está mergeado (`b3a6e53`), así que este trabajo está desbloqueado.

---

## 1. Lo que hay hoy en esa plancha

Medido corriendo el modelo, no leído del README. `au` = 528.02, alto = 248.18,
`t_piel` = 8, todo derivado de `params.scad`:

| y (mm) | qué vive ahí | ancho en x |
|---|---|---|
| 0.00 | canto de abajo = plano del suelo | — |
| 18.00 | fila de 5 M3 al larguero de base trasera | todo |
| 30.00 – 69.47 | **rejilla de entrada de aire + recorte del IEC** | todo |
| 83.47 – 115.47 | onda triángulo / onda cuadrada | 52.8–237.6 / 290.4–475.2 |
| 164.94 – 196.94 | onda sierra | 79.2–448.8 |
| 238.18 | fila de 5 M3 al larguero de remate trasero | todo |
| 248.18 | techo de la plancha | — |

La envolvente de una onda es `vent_periodo*0.35 + vent_ancho_ranura/2` — la
amplitud **más** medio ancho de ranura, porque la onda es un *hull* de círculos
y su borde de material asoma por debajo de la polilínea. Es el mismo término que
`piel_trasera_2d()` ya usa para calcular `lib1`
([`sam17_case.scad:506`](../../../case/cad/sam17_case.scad)); olvidarlo fue lo
que hizo que los 14 mm de `vent_separacion` salieran 12 la primera vez.

**Hueco de verdad libre**, ni ranura ni onda ni fila de tornillo:

| franja | y | alto | x utilizable |
|---|---|---|---|
| A | 0 – 18 | 18.00 mm | todo el ancho |
| C | 115.47 – 164.94 | **49.47 mm** | 0–79 y 449–528 enteros; en medio lo parte la sierra |
| D | 196.94 – 238.18 | **41.25 mm** | todo el ancho |
| E | 238.18 – 248.18 | 10.00 mm | todo el ancho |

Las dos franjas grandes son C y D. Juntas —si se retirara la sierra— darían
122.72 × 528.02 mm.

---

## 2. Cinco hallazgos

### 2.1 La regla de seguridad del mains se rompió, y nadie lo cantó — BLOQUEANTE

La spec del case §7 dice, textual:

> El cableado de 230 V vive solo en ese bloque y llega al transformador del
> módulo 1 […] **Las pieles removibles nunca llevan mains.**

Ese «ese bloque» es el *bloque trasero fijo del piso inferior*. **Ese bloque no
existe en el modelo.** Busqué `mains`, `230`, `bloque` y `esparrago` en
`sam17_case.scad` y `params.scad`: lo único que sale es el espárrago de PE, y
vive en la pared del **chasis de acero**, no en un bloque de la trasera.

Lo que sí existe es un recorte de IEC dentro de `piel_trasera_2d()`
([`sam17_case.scad:514-518`](../../../case/cad/sam17_case.scad)) — o sea en la
plancha que se quita con 10 M3, la que el orden de ensamblaje numera como paso 7.

No es un detalle de dibujo. El SAM17 es un aparato **Clase I** con entrada IEC
C14, y la regla de §7 existe justo para que desmontar una pieza no ponga a
nadie con los 230 V en la mano ni le cuelgue el cable de red de la propia
plancha que acaba de soltar.

O la regla está vieja y hay que reescribirla a conciencia, o el modelo está
mal. Lo que no puede quedarse es implícito.

### 2.2 La pieza de red SÍ está elegida, y el case era el último en enterarse

**Corrección de una versión anterior de este documento**, que decía que no había
pieza (Principio VII). La hay, con hoja y con BOM:

**Schurter KM00.1105.11** — clase I, portafusibles bipolar, interruptor bipolar,
sin filtro EMC. Vive en
[`hardware/01-power-supply/v3/bom-chasis.csv`](../../../hardware/01-power-supply/v3/bom-chasis.csv),
y `hardware/01-power-supply/v3/check_red_chasis.py` **lleva tiempo saliendo
HUECO** con este texto exacto:

> el recorte del KM00.1105.11 no esta en case/cad/params.scad. Hacen falta
> `chasis_iec_ancho` = 28.0 y `chasis_iec_alto` = 47.0 (esquinas R 0.3 max,
> hoja typ_KM.pdf p.3), con 29.35 mm libres detras de la pared

Una puerta del proyecto llevaba tiempo pidiéndole un número al case, y el case
no contestaba. De la hoja `typ_KM.pdf`:

| | |
|---|---|
| espesor de panel (snap-in) | **1 / 1.5 / 2 / 2.5 mm** (p.1) |
| recorte | 28 (+0.10/−0.05) × 47 (+0.10/−0.05), esquinas R ≤ 0.3 (p.3) |
| brida | 30.5 × 50, sobresale 2.5 del panel |
| cuerpo por detrás | 26.15 + 3.2 de clips = **29.35 mm** |

**La primera fila cierra la discusión de §2.1 sola.** El snap-in agarra chapa de
1 a 2.5 mm y la trasera tiene **8**. Esa pieza **nunca pudo montarse en el
acrílico**. La decisión D1 no era una preferencia: era la única lectura posible
de la hoja.

Y el 48 × 27.5 del `.scad` es **el recorte de la hoja girado 90° y redondeado a
ojo** (47 → 48, 28 → 27.5). Nadie escribió que fuera girado, y las dos cotas se
fueron de una tolerancia que la hoja da en centésimas.

### 2.2b El hueco estaba escrito a mano, y el propio código lo admitía

```
iec_alto = 27.5;                                    // sam17_case.scad:501
// recorte IEC C14 con interruptor (bloque snap-in tipico
// 48 x 27.5; CONFIRMAR contra el datasheet de la pieza comprada).
square([48 + kerf, iec_alto + kerf]);               // sam17_case.scad:518
```

El #130 decía *«Sin pieza elegida, el hueco es un número inventado»*. La
primera mitad resultó falsa (§2.2) y la segunda, verdadera de todos modos: el
hueco no se derivaba de la pieza que sí existía. Y agrava:

- **48 y 27.5 no están en `params.scad`.** Son literales del `.scad`.
- **Ninguna puerta los mira.** `clearance_budget.py` usa el 48 y el 70 para
  saltarse columnas de rejilla ([línea 785](../../../case/clearance_budget.py)),
  no para verificar el recorte.
- **El mismo número vive en tres sitios**: `au - 70` y el `48` aparecen dos
  veces en el `.scad` y una en el budget.

Ese último punto es el patrón que ya costó una tanda: el `- 15` de la trasera
estaba copiado en cinco sitios y ninguno sabía dónde estaba el suelo. Aquí hay
tres copias de un número que además nadie ha confirmado contra una pieza.

### 2.3 El #167 se contradice a sí mismo con el USB

La decisión 3 manda a la trasera *«USB device, USB host, MIDI DIN in/out,
clock/reset in/out, pedal»*. La tabla del mismo issue pone el USB en la columna
**«Se queda pegado a su placa»**, con su razón: *«señal rápida y puerta de la
masa sucia»*.

Se reconcilian de una sola manera: que atrás **haya una placa**. Los conectores
se mudan, pero siguen montados en cobre, no colgando de cables sueltos.

Si esa es la lectura correcta, el #167 crea una **tarjeta de E/S trasera** que
no nombra en ningún sitio — y con ella su alimentación, su masa, su cable plano
al cerebro y su sitio en el `power_budget`. Si no es la lectura correcta,
entonces el USB *no* se muda y son siete conectores, no nueve.

**Esto lo decide Samuel, no el modelo.** Y hasta que se decida, la trasera no se
puede cotar: una placa atrás necesita separadores, fondo y una ventana de
montaje; nueve conectores con cable suelto no necesitan ninguna de las tres.

### 2.4 Los nueve conectores no caben donde el issue supone

El #167 dice que hay que dar *«sitio, guarda y alivio de tracción a los nueve
conectores»*. Con las franjas de §1 delante:

- La franja **C** (49.47 mm) está partida por la sierra: quedan dos islas de
  ~79 mm de ancho en los extremos. Un DIN-5 no cabe cómodo en 79 mm junto a
  otra cosa.
- La franja **D** (41.25 mm) es la única continua de los 528 mm de ancho.
- La banda de abajo ya está tomada por la rejilla de aire, que no es adorno:
  es la entrada del tiro natural, y bajarla o encogerla mueve los 6.6 K.

Traducido: **los nueve conectores caben en D, o hay que negociar con una onda.**
Y las tres ondas son la firma visual del case — el README las llama así, y la
spec §7 las nombra como requisito de diseño, no como decoración.

### 2.5 Dos guiones que el #167 y el #152 dan por existentes, y no existen

- **`panel_budget.py` no existe.** Busqué en todo el repo: solo está
  `case/clearance_budget.py`. El #152 dice que `panel_budget.py` *«importa este
  diccionario»* y la spec del cerebro §10 describe lo que hace. Es futuro, no
  presente. Bueno saberlo: significa que el censo desactualizado del #152 **no
  está haciendo daño hoy**, y que arreglarlo es barato ahora y caro después.
- **El #103 mide una canaleta que ya no existe.** Su tabla reparte canales entre
  *siete* largueros e incluye `entrepiso trasero`, `repisa`, `piel_inferior` y
  `piel_superior`. Todas esas piezas murieron el 2026-08-21: hoy son **cinco**
  largueros y una sola trasera. Los «8,5 m de canaleta» son de otra geometría, y
  este trabajo va a meter cables nuevos justo por ahí.

---

## 3. Las decisiones — tomadas el 2026-08-23

Estaban tomadas **por omisión**, que es la peor manera de tomarlas. Samuel las
cerró en sesión el mismo día:

### D1 — la entrada de red se monta en una pieza fija

El conector sale del acrílico. Lo sostiene una pieza propia, atornillada a
estructura que **no se va cuando la trasera se destornilla**; el acrílico se
queda con una **ventana de paso**.

Y aquí cayó el segundo hallazgo geométrico. El #107 pedía montarlo en el chasis
de acero, *«montada en la propia caja»*, y **no llega**:

| | x |
|---|---|
| cara exterior de la trasera | 308.94 |
| cara interior de la trasera | 300.94 |
| largueros traseros (2020) | 280.94 – 300.94 |
| pared trasera del chasis de acero | 277.94 |

Son **23.00 mm** del chasis a la cara interior del acrílico, y **20 de esos 23
son el larguero de base trasera**, que va en medio. No hay línea recta: montarlo
en el chasis obligaría a atravesar una barra de 20 × 20.

Lo que sí está detrás de esa ventana y se queda puesto es **el larguero de base
trasera** (y = 8.00 – 28.00). La ventana empieza en y = 35.98, o sea **7.98 mm
más arriba**: un soporte atornillado a la ranura de ese 2020 la alcanza subiendo.

**Lo que esta decisión regala.** La cota exacta se muda del acrílico al metal.
El acrílico —lo caro, lo que no se deshace— pasa a llevar un hueco holgado, y el
metal, que se rehace barato y se hace después, se lleva el encaje. El #130 deja
de bloquear el corte de las planchas.

**Lo que esta decisión cobra**, y va anotado para que no se pierda:

- El conector queda **8 mm metido** (el espesor del acrílico), así que la
  ventana tiene que dejar pasar **el enchufe del cable**, no solo la cara del
  conector. Es más grande de lo que uno dibujaría a la primera.
- El acrílico naranja es traslúcido y un soporte metálico detrás se va a leer
  como **cuadro oscuro** — el mismo problema que mató la rejilla de aire en el
  suelo, y el riesgo 2 del #103. Hay que resolverlo; no hoy.

### D2 — los nueve conectores van en una tarjeta de E/S trasera

Montados en cobre, no colgando de cables, con un cable plano al cerebro. Es la
lectura que hace al #167 coherente consigo mismo: el USB *«se queda pegado a su
placa»* y la placa se muda con él.

**Consecuencias que el #167 no nombra y hay que abrir:**

- Es una **tarjeta nueva**, con su masa, su alimentación y su renglón en el
  `power_budget`.
- La trasera deja de necesitar solo agujeros: necesita **fondo, separadores y
  ventana de montaje**.
- Y ese fondo **se lo disputa con los módulos**. La franja D (y = 196.94 –
  238.18) tiene entre **60.00 y 101.24 mm** de la cara interior del acrílico al
  plano del panel de la fila de arriba — pero cuánto de eso se comen los módulos
  es exactamente el [#44](https://github.com/sssamuelll/sam17/issues/44), que
  sigue abierto. **La tarjeta trasera hereda esa dependencia.**

### D3 — sigue abierta, y ya no bloquea

¿IEC C14 o prensaestopas? Con D1 cerrada, esta decisión dejó de mandar sobre el
acrílico: cambia la pieza fija, no la plancha. Se decide cuando haya datasheet.

---

## 4. Lo que sí está bloqueado, y por qué

**La entrada de red ya no está bloqueada por compra** (§2.2): la pieza y su hoja
existen. Está bloqueada por una **decisión de geometría**, que es distinta y es
de Samuel:

Con la brida en el plano del acrílico, el cuerpo de la KM00.1105.11 llega a
x = **271.59** y la pared trasera del chasis de acero está en x = **277.94**:
**6.35 mm de interferencia**. Y los dos se solapan en horizontal por los 48 mm
enteros de la ventana (el chasis ocupa x = 179.42 – 518.02 del ancho).

Las salidas, sin recomendar ninguna todavía:

| | qué cuesta |
|---|---|
| Alivio local en la pared trasera del chasis | Un recorte más en una pieza de chapa que ya lleva varios. Y deja los bornes de red **dentro** de la caja de acero puesta a tierra, que para un Clase I es lo que uno quiere |
| Adelantar el chasis 6.35 mm | No cabe: la puerta ya reporta *«3.00 mm delante y 3.00 detrás (mínimo exigido 3)»*. Se comería el mínimo |
| Montar el módulo en la pared del chasis y no en el plano del acrílico | Es lo que pide el #107, y **no llega**: el enchufe quedaría 31 mm metido y el larguero de base trasera se atraviesa |

**Los nueve conectores de la trasera sí siguen bloqueados por compra.** La spec
del cerebro §6 los nombra por familia (USB-B, USB-A, DIN-5 ×2, Thonkiconn
WQP-PJ398SM ×4, jack de 6,35 mm) y solo uno tiene referencia exacta —el
Thonkiconn, «la misma pieza que el módulo 3»—. Una familia no tiene cota de
recorte, y no las voy a estimar: este repo ya tiene el caso del toroide, 45 mm
heredados sin fuente, «corregidos» a 52.1 con dos listados de distribuidor
coincidentes, y la hoja del fabricante dijo 46 (PR #126).

---

## 5. Lo que propongo tocar, y en qué orden

De a una, cada una revisada antes de la siguiente:

1. ~~**Cerrar D1**~~ — **hecho** (2026-08-23). Ver §3.
2. ~~**Cerrar D2**~~ — **hecho** (2026-08-23). Ver §3.
3. ~~**Parametrizar la ventana de la entrada de red**~~ — **hecho**.
   `iec_ancho`, `iec_alto` e `iec_margen_der` viven en `params.scad`, una sola
   fuente para los tres sitios que los copiaban, y `guarda_red()` en
   `clearance_budget.py` los vigila. Detalle en §6.
4. **Corregir el censo del #152** antes de que `panel_budget.py` lo importe.
   Barato ahora, caro después.
5. **Actualizar la tabla de canales del #103** a los cinco largueros que hay,
   porque los cables de estos nueve conectores van a pedir sitio ahí.
6. **Dibujar la pieza fija de la entrada de red**, y con ella la ventana de paso
   de verdad. Necesita el datasheet (§4).
7. **Abrir el hueco de la tarjeta de E/S trasera**: fondo, separadores y ventana
   de montaje — encadenado al #44, que decide cuánto fondo dejan los módulos.

Los pasos 4 y 5 no dependen de ninguna compra. El 6 depende del datasheet y el
7 del #44.

---

## 6. Lo que ya está hecho en el modelo

**Solo estructura, cero geometría.** La ventana de la entrada de red eran dos
literales (`48` y `27.5`) escritos dentro de `sam17_case.scad`, y el mismo
número copiado en tres sitios: dos en el `.scad` y uno en `clearance_budget.py`.
Ninguna puerta los tocaba.

Ahora:

- Los tres valores viven en `params.scad`, rotulados **SIN DERIVAR de la
  KM00.1105.11**, con su hoja citada y las tres razones por las que **no** se
  «corrigen» a 47 × 28: el número de la hoja está girado sin decirlo, esta
  ventana ya no es un recorte de encaje sino un paso, y hay un choque de 6.35 mm
  sin resolver (§4). Pasar de un número inventado a uno **prestado de otra pieza
  del ensamblaje** sería peor: parecería derivado. Se quedan visibles y rotos
  (Principio V).
- `iec_margen_der = 22` sustituye al `au - 70`, que era el canto *izquierdo*
  contado desde la derecha — un número que no quería decir nada. Ahora es una
  distancia al canto, que es lo que de verdad importa en una plancha de PMMA.
- `rejilla_entrada()` recibe la x de la ventana en vez de rederivarla, por la
  misma razón por la que ya recibía la banda `(y0, y1)`: rederivarla fue lo que
  dejó el número copiado tres veces.
- `guarda_red()` exige tres cosas y **declara** que la cota es provisional:

```
entrada de red: ventana de 48.0 x 27.5 en x=458.02..506.02, y=35.98..63.48
  5.98 mm de puente arriba y abajo, 8.98 contra la ranura mas cercana, 22.0 al canto derecho
  PROVISIONAL, sin datasheet (#130): el conector NO se encaja aqui -- lo sostiene
  una pieza fija atornillada al larguero de base trasera, 7.98 mm mas abajo
```

- **`_banda_libre_trasera()`** — la banda entre la fila de M3 y la onda estaba
  calculada en dos sitios y ahora la piden tres. Una sola fuente.
- **`canario_red()`**, porque el Principio VIII lo exige y porque hizo falta:
  la primera versión de `guarda_red()` tenía **tres** asertos y el segundo **no
  podía fallar nunca**. Aseveraba el puente contra la ranura más cercana, que es
  la misma desigualdad con la que `_rejilla_entrada()` decide saltarse esa
  columna — o sea, le preguntaba a la regla si cumplía la regla. Verde con
  cualquier parámetro, incluso con la geometría rota. Se borró y en su lugar
  quedó la nota que explica por qué no está.
- **`case/**/check_*.py` entra en `hardware/tools/gates.py`.** `check_dxf.py`
  no estaba en ningún patrón: el glob del case solo recogía `*_budget.py`. Era
  el único guion que **relee los DXF exportados** — el artefacto que se manda al
  taller, no el modelo que lo genera — y no corría en la suite. Es literalmente
  el aviso que `CONTRIBUTING.md` da: *«un guion que el gate no ve no es un
  gate»*.

**Verificación.** Tres cosas, en orden de lo que costaría equivocarse:

1. **El DXF no se movió.** Se reexportó `piel_trasera_2d` y el SHA-256 sale
   **idéntico** al fichero commiteado (`abfecd56…d21881`) — que es el criterio
   que el README manda para la clase DXF. Las cifras de aire (6 950 mm², 45
   ranuras, 6.6 K) también, byte a byte.
2. **El gate nuevo distingue.** Las dos mutaciones lo ponen rojo: `iec_alto` a
   31.97 (se come el puente contra la onda, que es el desenlace probable del
   #130) y `iec_margen_der` a 3.5 (pegada al canto). Con los parámetros de
   verdad, verde.
3. **Y el canario caza una puerta ciega.** Sustituyendo `guarda_red` por una
   función que no mira nada, `canario_red` la denuncia. Es la mitad que el
   propio repo vio fallar con el `.netgold`.

---

## Lo que este documento NO decide

El reparto de placas, el J2, las masas separadas y la doctrina de módulos —el
#167 ya dice que no los toca—. Tampoco el ancho del panel del cerebro, que sale
de `panel_budget.py` cuando exista. Ni el trazado fino de cada bajada de cable,
que sigue dependiendo del #44.
