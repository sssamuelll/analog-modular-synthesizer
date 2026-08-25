# Constitución del SAM17

Sintetizador analógico modular polifónico de 16 canales, reconstruido a partir
de una tesis de grado y llevado más allá de ella.

Estos principios no son buenas intenciones: cada uno está aquí porque su
ausencia ya costó trabajo perdido en este repositorio. Se citan los casos.

---

## Principios

### I. Todo número va contra fuente primaria, o va a «lo que NO está confirmado»

Un dato de un componente se verifica contra el **datasheet del fabricante y del
encapsulado exacto que se compra**. Lo que no se pueda verificar así **no se
suaviza con un "debería ir bien": se escribe en la sección de lo no confirmado**,
con qué habría que medir para cerrarlo.

Por qué, con los casos que lo enseñaron:

- El LM2940-12 no pide `12 V + dropout` sino **13.6 V garantizados**. La
  simulación daba 13.53 y fallaba por 70 mV sin que se notara.
- El pinout TSSOP del AD5686R **no es el del LFCSP**: van desfasados dos pines.
- El grado `-EP` del mismo chip es **peor** que el comercial pese a llamarse
  *enhanced*. Se usaron sus números un rato por haber abierto ese PDF primero.
- El orden de filas del peine Eurorack sigue sin cerrarse contra tabla oficial,
  y por eso es el issue #15 y no una suposición enterrada en el código.

### II. Cada presupuesto es un script ejecutable con aserciones, no prosa

Un número en un párrafo envejece en silencio: alguien cambia un ancho de cobre y
el párrafo sigue diciendo lo mismo. Un script se rompe en voz alta.

Todo margen que decida un diseño — afinación, masa, térmica, dropout, acoplo —
vive en un `*_budget.py` con:

- las constantes con su unidad y de dónde salen,
- una **autocomprobación** del propio cálculo contra un caso hecho a mano,
- **aserciones que fallan** si el diseño se sale del presupuesto,
- y un bloque explícito de lo que el cálculo *no* cubre.

Precedentes: `ground_budget.py`, `tuning_budget.py`, `autotune_budget.py`,
`hum_loop.py`. Los cuatro han cazado errores reales, incluidos errores propios
del cálculo.

### III. Una comprobación que pasa sobre un artefacto vacío no es una comprobación

Las comprobaciones van **antes** del paso destructivo, no después.

Caso: `create_schematic` trunca el fichero nada más empezar. Una aserción
posterior dejaba una hoja **vacía** en disco — y una hoja vacía pasa el ERC con
**0 errores y 0 avisos**. Se commiteó un esquemático de 711 bytes que parecía
perfecto. Desde entonces `check_footprints()` corre antes de tocar nada.

Corolario: un script que deja el trabajo a medias **sale con código de error**.
`build_pcb.py` del módulo 2 sale con 2 mientras queden redes sin rutear,
precisamente para que no se confunda con terminado.

### IV. Se comprueba lo que importa, no un proxy cómodo

Un proxy es una regla que se parece a lo que quieres y no lo es. Pasa el test y
te deja tranquilo con el problema intacto.

- «Nada de pistas por B.Cu en el lado analógico» era un proxy. Lo que hace daño
  no es que haya cobre abajo, es que **el plano quede partido**. La regla buena
  cuenta las islas del vertido.
- Comprobar pista contra pista y no **pista contra pad** dejó un ruteo que
  parecía limpio y del que el DRC sacó **5 cortos**.
- Modelar un pad como círculo de su dimensión mayor convertía un pad TSSOP de
  1.5 × 0.4 en un obstáculo de radio 0.75 que tapaba a sus vecinos.

### V. Un fallo invisible es peor que un hueco visible

Entre dejar trabajo sin terminar y terminarlo mal, se deja sin terminar.

Caso: el ruteador de laberinto bajó las redes sin rutear de 17 a 13 **a cambio
de 18 posibles cortos**. Se revirtió. Un cable que falta lo marca la herramienta
en rojo; **un roce de 0.05 mm no se ve**, se fabrica, se suelda y aparece como
"el aparato hace cosas raras".

Ninguna regla de seguridad se afloja para que quepa el ruteo. Ni la barrera de
red, ni la separación entre masas, ni las distancias de fuga.

### VI. Lo aplazado se abre como issue con evidencia

Lo que no se cierra no se deja en un comentario ni en la cabeza de nadie: se
abre como issue con el número que falta, cómo medirlo y cuál es el criterio de
cierre. Cada tanda se cierra **mergeada**.

### VII. Los errores propios se corrigen en voz alta

Cuando un número publicado resulta estar mal, se dice y se explica de dónde
salía el error — no se edita en silencio.

Precedentes: los «40-80 cents» del daisy-chain que en realidad eran 6.3 con
contacto bueno y 29.7 con Dupont; un estimador de área que daba 7.82 cm² siendo
su propia cota superior 6.81, que es imposible.

### VIII. Una comprobación que nunca se ha visto fallar no es una comprobación

El Principio III dice *cuándo* corre una comprobación. Este dice si de verdad
**distingue** una placa buena de una rota. Y eso no se razona: se prueba
rompiendo a propósito lo que vigila y viendo el gate ponerse rojo.

Todo gate nuevo — `check_*.py`, `*_budget.py`, un golden, una aserción dentro de
un generador — nace con su **mutación**: la modificación mínima que tiene que
hacerlo fallar. Si la mutación pasa en verde, el gate no vigila nada.

Casos:

- La mutación del `.netgold` **no falló**. La cadena de prueba estaba mal
  construida (le faltaba un pin) y el verde era un verde vacío: el golden llevaba
  tiempo sin mirar lo que decía mirar. Es el Principio III mordiendo a la propia
  herramienta.
- `run_sim.py` encontraba una esquina fuera de regulación y **salía en verde**.
  Corolario: un gate que halla algo **sale rojo**. No basta con que no explote.
- Un generador que falla **no puede vaciar el artefacto**: se mide el tamaño del
  fichero antes y después de forzar el error (181 785 B las dos veces), porque
  una hoja vacía pasa el ERC con 0 avisos.

### IX. Lo que ninguna medida numérica ve, lo ve el ojo — y el ojo es una puerta

Hay una clase de defecto que no tiene check: el que vive en la geometría de las
piezas y no en el cobre. Ninguna aserción de este repositorio lo mira, y no es
por falta de escribirlas.

Caso: **el cuerpo de RV1 montaba sobre la ranura.** Los pads estaban donde
tocaba, el DRC en cero, el netlist correcto, todas las distancias dentro de
presupuesto. *«Esto no lo ve ninguna medida de cobre — lo vio el render.»* En la
misma revisión, J5 al aire.

Por eso el render **no es cosmética ni documentación**: es un gate del proceso.
Cada tanda de hardware exporta la vista 2D y el render 3D, y **una persona los
mira antes de cerrar**. Que el ojo humano no se pueda automatizar no lo convierte
en opcional: lo convierte en el único gate de su clase.

Corolario: los renders se commitean con la placa. Un gate cuyo resultado no queda
en el repositorio no se puede volver a revisar.

---

## Cómo se construye el hardware

- **El artefacto es el script.** Los `.kicad_sch` y `.kicad_pcb` se **generan**
  desde `build_schematic.py` y `build_pcb.py` y se pueden borrar y rehacer. Lo
  que se revisa en un PR es el script, no el s-expr.
- **Las razones viven en `notes/design-notes.md`** de cada módulo, en secciones
  numeradas que se añaden sin reescribir las viejas, y con una sección final de
  lo no confirmado.
- **El símbolo y la huella se verifican contra disco** en cada build.
- **El netlist se contrasta contra el diseño declarado a mano.** El ERC a cero
  solo dice que no hay conflictos: una hoja con +12 V y −12 V intercambiados pasa
  el ERC con cero avisos y fríe todos los módulos que se enchufen.

## Puertas de calidad

Ninguna tanda de hardware se da por cerrada sin todo esto en verde:

| | |
|---|---|
| ERC | **0 infracciones** |
| DRC | **0 infracciones y 0 elementos sin conectar** |
| Netlist | contrastado pin a pin contra el diseño declarado aparte, **y su firma canónica sin cambios respecto al `.netgold` commiteado** |
| BOM | cruzado en los dos sentidos con los designadores de la hoja |
| Presupuestos | todos los `*_budget.py` en verde |
| Mutación | cada gate **nuevo o tocado** en esta tanda, visto fallar con su mutación (Principio VIII) |
| Render | vista 2D y render 3D exportados, **mirados por una persona** y commiteados (Principio IX) |

Y para el firmware: nada sin test que falle antes de existir la implementación.

**Quién hace cumplir esto: `python hardware/tools/gates.py`.** Durante la
primera tanda larga de hardware estas puertas las hacía cumplir la memoria de
quien mandaba el PR, y trece scripts con aserciones reales vivían en el repo sin
que nada los ejecutara. Una puerta que depende de que alguien se acuerde no es
una puerta.

> **Estado 2026-08-17: se corre a mano.** El workflow de CI incluye el job
> (`.github/workflows/ci.yml`), pero **GitHub Actions está deshabilitado a nivel
> de repositorio**, así que hoy no corre nada automáticamente — tampoco el job
> de firmware. Hasta que se active, `gates.py` antes de cada PR es obligatorio y
> el PR dice su resultado. Esto se anota aquí, y no en un comentario del
> workflow, porque es justo la clase de cosa que se olvida y deja a todo el
> mundo creyendo que hay una red debajo.

El runner descubre los gates **por patrón** (`check_*.py`, `*_budget.py`,
`simulations/*/*.py`), no por lista: un gate nuevo se añade escribiendo el
fichero. Una lista habría que acordarse de ampliarla, y el día que a alguien se
le olvide, el gate nuevo nace ya sin correr.

Y distingue tres estados, no dos. Lo que no se puede comprobar sale como
**HUECO con el motivo escrito** y se cuenta en el resumen: no rompe el CI, pero
tampoco se disfraza de verde. Un `skip` silencioso consigue las dos cosas a la
vez — ni corre, ni te enteras — que es el Principio V con otra ropa.

## Los números que gobiernan el instrumento

Cambiar cualquiera de estos obliga a revisar el presupuesto que lo sostiene:

| | |
|---|---|
| 1 V/octava | **1 mV = 1.2 cents**. Es la constante de la que cuelga todo |
| Suelo de afinación | **1.71 cents**, y son masa del bus (1.21) + medida (0.50) |
| Rieles | ±12 V a **650 mA**; +5 V acotado a **300 mA** por diseño |
| CV de tono | **0–7 V**, 7 octavas (cambio respecto a los 3–10 V de la tesis) |
| Masas | `GNDA` y `GNDD` se unen **solo** en la estrella del módulo 1 |
| Voces | **4**, con mandos compartidos y circuitos replicados |

## Gobierno

Esta constitución está por encima de cualquier costumbre del repositorio. Todo
PR se revisa contra ella, y si un principio estorba se **enmienda aquí primero**,
con el motivo, en vez de saltárselo en un módulo.

Las enmiendas suben de versión: MAYOR si se quita o se invierte un principio,
MENOR si se añade uno, PARCHE si es redacción.

Los principios I a IX son **innegociables**. El resto son convenciones y se
pueden discutir.

**Versión**: 1.1.0 | **Ratificada**: 2026-08-15 | **Última enmienda**: 2026-08-21

> **1.1.0** (MENOR, dos principios nuevos): se añaden el **VIII** (todo gate se
> valida con una mutación que tiene que hacerlo fallar) y el **IX** (el render
> mirado por una persona es una puerta del proceso). Los dos salen de fallos que
> ya ocurrieron y que ningún documento del repositorio recogía: la mutación del
> golden que pasó en verde vacío, y el cuerpo de RV1 montado sobre la ranura con
> todos los checks numéricos en verde. Se añaden sus dos filas a las *Puertas de
> calidad*. Ningún principio anterior cambia.
>
> **1.0.1** (PARCHE, redacción): las *Puertas de calidad* dicen ahora quién las
> hace cumplir (`hardware/tools/gates.py`, en el CI) y qué es un HUECO. Se añade
> la firma canónica del netlist a la puerta que ya existía. Ningún principio
> cambia.
