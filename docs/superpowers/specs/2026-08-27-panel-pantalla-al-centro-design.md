# El panel gira alrededor de la pantalla — propuesta de reencuadre

> **Estado: PROPUESTA.** No toca código ni DXF. Revisa un paquete que
> Samuel firmó el 2026-08-23, así que lo que hay aquí no entra hasta que
> él lo firme o lo devuelva.

**Sujeto:** la fila superior del SAM17 deja de ser un reparto de módulos y
pasa a ser **un solo módulo del ancho del riel, con la pantalla de 7" en su
centro y todo lo demás organizado a su alrededor**.

**Origen:** dirección de Samuel, 2026-08-27, textual:

> «el diseño del panel gira alrededor de la pantalla. la pantalla va en el
> centro del panel y todo lo demas crece alrededor. entonces 7 pulgadas va
> in. todo lo demas se reformula al rededor. recuerda que toda la parte de
> arriba es un solo modulo. de ese largo. en el centro del modulo va la
> pantalla. al rededor. potenciometros que pueden ser parametrizables por
> el cerebro»

---

## 0. Por qué este papel existe

Porque la pregunta estaba mal planteada, y el error fue mío. Hasta hoy el
sitio de la pantalla se trató como un **problema de reparto**: hay 528,32 mm
de riel por fila, hay una lista de módulos que los piden, ¿sobra sitio para
una pieza de 165 mm? Con esa pregunta la respuesta es que no sobra, y de ahí
salió el informe equivocado del 2026-08-27 por la mañana.

La pregunta correcta no es de reparto sino de **jerarquía**: la pantalla no
compite por sitio con los mandos, es el objeto alrededor del cual los mandos
se ordenan. Cambia quién es el sujeto de la frase.

---

## 1. Lo que este papel NO decide

Se dice antes que nada, porque la mitad del valor está en no fingir que se
decidió:

- **Las conexiones.** Samuel las dejó abiertas en voz alta («luego
  decidiremos qué vamos a hacer con las conexiones»). §5 pone las dos
  opciones que él nombró con lo que cada una cuesta, y **no elige**.
- **Qué dibuja la pantalla.** Sigue siendo trabajo de diseño aparte, como ya
  decía `2026-08-26-pantalla-motor-design.md` §8.
- **El diámetro del cap de las macros**, que es la medición 3 del #179 y la
  que decide cuántas perillas esenciales existen.
- **La pieza concreta** de pantalla (R-M3: hoja en árbol antes de dibujar).

---

## 2. El lienzo, con los números

| Magnitud | Valor | Fuente |
|---|---|---|
| Riel por fila | **528,32 mm = 104 HP** | `params.scad: largo_riel`; Z-Rails Tiptop comprados |
| Alto de panel | **128,5 mm** (3U) | `params.scad: alto_panel_sup` |
| Pantalla | **165 × 102 mm** | `2026-08-26-pantalla-motor-design.md` §6 (clase Adafruit 7", 800×480) |

Con la pantalla centrada:

```
                     528,32 mm  (104 HP)
   |<--- 181,66 --->|<-- 165 -->|<--- 181,66 --->|
   |   FLANCO IZQ   |  PANTALLA |   FLANCO DER   |   128,5 de alto
   |                |  165x102  |                |
                     ^^^ franja de 13,25 arriba y abajo
```

- **Flancos: 181,66 mm cada uno (35,8 HP), a altura completa.** 363,32 mm de
  ancho de mandos en total.
- **Franjas arriba y abajo de la pantalla: 13,25 mm.** Es la cota que manda,
  y se dice fuerte: **ahí no cabe un potenciómetro**. La pantalla se come 102
  de los 128,5 de alto, así que **todo mando vive a izquierda o derecha**, no
  encima ni debajo. El único inquilino posible de esas franjas es serigrafía,
  luz o nada.

> **HUECO:** el issue #179 habla de un «campo vertical de 112,5 mm» y su
> derivación no está en el plan del panel ni en `params.scad`. Si el campo
> útil son 112,5 y no 128,5, las franjas caen a **5,25 mm** y la conclusión
> se endurece, no se ablanda. Hay que cerrarlo antes de dibujar.

---

## 3. La cuenta que decide si esto es posible

La fila A hoy mide **83 HP = 421,64 mm** y de ahí la bahía se lleva ~68 mm
(16 Thonkiconn en 4×4 a paso 17). Área de mandos actual: **353,64 mm**.

| | mm de mandos |
|---|---|
| Fila A hoy (83 HP menos la bahía) | 353,64 |
| Fila A propuesta (104 HP menos la pantalla) | **363,32** |
| Diferencia | **+9,68** |

**Sale, pero por los pelos, y sólo porque pasan las dos cosas a la vez:** el
panel crece de 83 a 104 HP **y** los jacks se van del panel. Cualquiera de
las dos sola no alcanza.

Y hay una ganancia que no está en esa tabla: el **RENGLÓN** —la ventana de
216 × 18 mm que hoy dice nombre y valor del último parámetro tocado— deja de
necesitar su banda horizontal, porque la pantalla hace ese trabajo mucho
mejor. Eso libera alto en los flancos, que es justo la dimensión escasa.

**Lo que NO cambia:** el PCB de la Voz cierra en 421,5 mm y **no tiene que
crecer**. Las perillas son sensores del panel, no componentes de la placa
(`2026-08-23-modulo-voz-total-design.md` §8), así que el panel puede volar
sobre el borde de la placa sin tocar el factor de ruteo — que es «el número
menos medido de todo el diseño» y conviene no tocarlo.

---

## 4. Lo que esto revisa del paquete firmado el 2026-08-23

`docs/superpowers/plans/2026-08-23-panel-frontal-gramatica.md` está **firmado
por Samuel** («dale pues»). Esta propuesta lo toca en cinco sitios y ninguno
se da por hecho.

| Lo firmado | Qué le pasa | Gravedad |
|---|---|---|
| **B2 — «una sola cabeza»** | La 7" al centro **es una segunda cabeza** salvo que sustituya a la 2,8" | **La decisión de fondo** — ver §4.1 |
| Fila A = **83 HP** | Pasa a **104 HP** | Media: el panel crece, el PCB no |
| **RENGLÓN** 216×18 | Lo absorbe la pantalla | Baja: mejora lo que el renglón hacía |
| **BAHÍA** 4×4 al canto derecho | Se va del panel (§5) | Media: **resuelve la colisión E-C6**, que sigue abierta |
| Fila B **CABEZA 30 HP** | Se libera si la 7" es la cabeza | Alta: son 152,4 mm que cambian de dueño |

### 4.1 B2 es la decisión de verdad, y no es de layout

El paquete firmado dice **una sola cabeza**, y el renglón sobrevivió sólo
porque se argumentó que «es etiqueta, no cabeza». Una pantalla de 7" al
centro del panel no admite ese argumento: es una cabeza, y de las grandes.

Así que B2 fuerza una bifurcación, y hay que tomarla explícitamente:

**Camino 1 — la 7" es LA cabeza.** La 2,8" de la fila B desaparece y con ella
los 30 HP de la zona CABEZA. B2 se mantiene intacta, sin re-firmar.
**Consecuencia arquitectónica: la cabeza se muda del cerebro al motor.** Hoy
la 2,8" cuelga del RP2350B por SPI (`2026-08-21-modulo-2-v2-cerebro-design`
§7) y la 7" cuelga del LTDC del N657 (`2026-08-26-pantalla-motor-design` §1).
Lo que la cabeza local hacía sin depender del motor —número de preset, canal
MIDI, si el autoafinado corre, qué operación retenida espera el dedo— pasaría
a depender de que el motor esté vivo. **Eso hay que presupuestarlo, no
suponerlo**: si el motor cae, ¿el instrumento se queda mudo de cara?

**Camino 2 — conviven las dos.** Hay que **re-firmar B2** contra sus tres
motivos originales (sobriedad, consumo, competencia visual). El de consumo no
es retórico: el presupuesto de +5 V ya no cierra hoy (#151) y no tiene guion,
y la 7" pide 450–550 mA con retorno dedicado.

**Recomiendo el camino 1**, y no por elegancia: porque el camino 2 pide
re-abrir una firma y además carga la pantalla grande encima de un presupuesto
de +5 V que ya está en rojo. Pero la consecuencia del camino 1 —la cara del
instrumento depende del motor— es exactamente el tipo de cosa que R-M5 obliga
a mirar de frente, y no la decido yo.

---

## 5. Las conexiones: las dos opciones que Samuel nombró

**No se elige aquí.** Se ponen los costos que ya están medidos, porque uno de
los dos tiene un problema que el propio plan del panel ya documentó.

### Opción A — el valle como patch bay

**Tiene una colisión térmica ya medida, y es seria.** El plan del panel puso
la bahía pegada al canto derecho por esta razón textual:

> «el mazo de cables se barre al costado y **no tapa el valle de ventilación**
> (con el valle tapado, el salto térmico pasa de 6,6 a 8,8 K)»

Poner el patch bay **en** el valle pone el mazo ahí por diseño, no por
accidente. Y el valle no es una salida cualquiera: de los 9 943 mm² de
salida de aire, **7 499 son del valle** (102 ranuras) — el 75 %.

No la mata: dice que la opción A necesita un camino de aire alternativo
declarado y medido **antes**, no después.

### Opción B — patch bay trasero, junto con alimentación e interfaz de audio

**Esta ya está medio decidida y a favor.** La decisión **D2, cerrada el
2026-08-23**, mudó los nueve conectores del cerebro a una **tarjeta de E/S
trasera** montada en cobre (issue #183, hijo del #167). Meter ahí también los
jacks de la bahía y la alimentación es la continuación natural de una
decisión que ya se tomó, no una idea nueva.

Lo que hereda si se elige, y está escrito:

- La tarjeta trasera **le disputa el fondo a los módulos** en la franja D
  (y = 196,94–238,18), y cuánto se comen los módulos es el **#44**, abierto.
- Necesita su masa, su alimentación y su renglón en `power_budget`.
- La trasera pasa de «agujeros» a **fondo, separadores y ventana de montaje**.

### Lo que las dos comparten

Los jacks dejan de estar en el panel, así que **la colisión E-C6 muere**: el
2×8 pedía 136 mm contra los 100 presupuestados y por eso se apretó a 4×4.
Fuera del panel, el paso deja de estar apretado.

---

## 6. Los mandos, y una consecuencia que Samuel nombró de pasada

Samuel dijo «potenciómetros que pueden ser **parametrizables por el
cerebro**». Eso no es un detalle de layout: es el **Principio 4** del plan del
panel («todo comportamiento es configurable, por modos de ejecución») dicho
otra vez, y ese principio ya tiene una deuda abierta contra él — Voronov
dictaminó que **el modelo no tiene eje de autoría**: `Set(id, valor)` no dice
quién escribe, así que «la perilla la mueve el cerebro» y «la perilla la mueve
la mano» son indistinguibles en el núcleo.

Con la pantalla al centro eso se agrava, porque ahora hay **tres** escritores
posibles sobre el mismo parámetro: la mano, el cerebro y el táctil. La deuda
es el issue **#177** («el núcleo tiene que saber quién escribe») y este papel
la nombra como **prerrequisito**, no como trabajo paralelo.

---

## 7. Qué habría que enmendar, con dueño

Se listan con dueño y no se mandan al aire: en este repo las tablas de
enmiendas mandadas y no ejecutadas ya son un patrón conocido.

| Papel | Sección | Qué cambia | Dueño |
|---|---|---|---|
| `2026-08-23-panel-frontal-gramatica.md` | §4, §9 | Fila A a 104 HP; el renglón se disuelve; la bahía sale; B2 según §4.1 | este papel, al firmarse |
| `2026-08-23-modulo-voz-total-design.md` | §8 | El reparto fila A / fila B deja de ser cierto | este papel, al firmarse |
| `2026-08-26-pantalla-motor-design.md` | §6 | «Sitio en el case: fila mandada» **queda contestada**: centro del panel de la fila A | este papel, al firmarse |
| `case/clearance_budget.py` | censo | `ANCHOS_PISO_*` deja de tener sentido: la fila A es un módulo, no una lista | PR #221, a rehacer |
| `hardware/03-vco/voz_total_budget.py` | — | Le falta `ANCHO_PANEL_A`, ya señalado en el plan §8 | el plan del panel |
| `case/README.md` | l.508, «BOM de herrajes» | Sigue diciendo «Censo actual de paneles: 8» | PR #221 |

---

## 8. Lo que hay que medir antes de dibujar

1. **El campo vertical real de una fila 3U en este case.** 128,5 es el alto de
   panel; el #179 habla de 112,5 sin derivarlo. De ese número depende si las
   franjas de la pantalla son 13,25 o 5,25 mm.
2. **La profundidad de la pantalla contra el fondo de la fila A**, que el plan
   del panel ya declara **al 100 %** con los potes dentro (E-C5, 0,6 mm de
   margen). Una pantalla de 7" con su cinta y su placa no entra en 0,6 mm de
   sobra: esto puede ser el bloqueante de verdad, más que el ancho.
3. **Las tres mediciones del #179**, que siguen siendo la puerta del congelado
   y que esta propuesta **no sustituye**: el frente muerto a 45°, el capacitivo
   a través del espesor, y el diámetro del cap.

El punto 2 es el que más miedo debería dar, y por eso está escrito.
