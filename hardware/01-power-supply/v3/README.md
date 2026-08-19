# PSU v3 — la primera que se construye

**Estado:** Fases A (decisiones), B (esquemático), D (chasis) y la colocación
de la Fase C cerradas. Faltan el ruteo y la validación.

> **La v1 y la v2 son diseños de papel.** La v1 se abandonó el 2026-08-17 sin
> fabricar; la v2 llegó a tener gerbers, BOM y CPL generados y tampoco se pidió.
> Ésta es la tercera y la primera que existe como objeto. De ahí su constraint:
> **lo que no quede decidido sale con huella y `DNP`, nunca con una v4.**

## Qué cambia respecto de la v2

La topología de regulación **no se toca**: sigue siendo la cascada de dos etapas
por riel, con las mismas piezas y los mismos setpoints. Lo que cambia es todo lo
que la rodea.

| | v2 | v3 | por qué |
|---|---|---|---|
| **Disipación** | 3 disipadores Fischer individuales | los tabs contra la pared del chasis | Tj de `U2`: 101 → **62 °C** |
| **Colocación de los TO-220** | diagonal opuesta a la isla SMD | en fila sobre un canto, **tabs coplanares** | lo impone la pared, no la estética |
| **Protección** | crowbar en +12 V | **ninguno, en ningún riel** | #118 |
| **Instrumentación** | 6 test points | test points + **isla de telemetría** | spec §4 |

### La protección: no se sustituye, se retira

El crowbar de la v2 protegía contra un fallo del regulador que pusiera VRAW en
el bus. Al rehacer el análisis contra el BOM real (§16.8, reescrita) salieron dos
cosas a la vez:

- **La cascada ya protege sola.** Ningún fallo *simple* pone más de ±13,1 V en el
  bus, que está dentro del máximo absoluto de todos los chips del instrumento. Y
  el pre-regulador no arrastra al post: los LT3045/LT3094 aguantan los 20,54 V de
  VRAW con 1,46 V de margen (ADI Rev. D p.2 / Rev. B p.3).
- **El lazo del crowbar no cerraba con ningún SCR.** El fusible tiene que abrir
  para que el corto sirva de algo, y `F1` subió de 250 mA a 1,6 A en la v2 —
  correctamente, por el inrush del toroide. A los 2,79 A que refleja el fallo,
  IEC 60127 **no obliga** a un fusible T a abrir. El SCR muere en 140 µs; el
  fusible tarda entre 1,3 y 3,9 s.

> El fallo del guardaespaldas es peor que el peligro del que cuida.

Lo que **no** se va con el crowbar: **un TR1 sin fusible térmico embebido no se
compra.** Los 642 W de cualquier corto del secundario son la cuenta que ni `F1`
ni un crowbar cubren, y esto pasa dentro de un recinto cerrado.

## Las puertas

Cuatro, todas ejecutables, todas recogidas por `hardware/tools/gates.py` sin
tener que apuntarlas en ninguna lista:

| Puerta | Qué pregunta |
|---|---|
| [`check_absmax.py`](check_absmax.py) | ¿sobreviven los módulos a un fallo de regulador? Y antes de eso: ¿la cascada **existe**? |
| [`check_telemetria.py`](check_telemetria.py) | ¿el instrumento sobrevive a medir? Divisores, shunts, direcciones I²C y alimentaciones contra el límite garantizado de cada datasheet |
| [`kicad/check_bom.py`](kicad/check_bom.py) | ¿el BOM y la hoja tienen los mismos designadores? |
| [`kicad/check_netlist.py`](kicad/check_netlist.py) | ¿la isla está **cableada** como dice el contrato? Shunts en serie, divisores en el sentido correcto, masas sin un nodo común |
| [`kicad/check_pcb.py`](kicad/check_pcb.py) | ¿la placa **commiteada** está colocada como dice el script? Y la barrera de red, la isla de referencia, la diagonal del lazo y los tres tabs contra la pared |

Las tres primeras se reparten huecos a propósito: `check_bom.py` pasaría en
verde con SDA y SCL cambiados —no falta ni sobra un componente, sobra un cable
en el sitio equivocado— y por eso existe la de netlist.

Y `check_pcb.py` cierra uno más viejo. `gates.py` sabía buscar el Python de
KiCad desde hace versiones (`necesita_kicad` / `PY_KICAD`) y **no había un solo
fichero que lo usara**: ni la v1 ni la v2 tuvieron nunca la placa dentro de la
suite. Todas sus comprobaciones —barrera de red incluida— corrían solo cuando
alguien se acordaba de ejecutar `build_pcb.py` a mano.

Lee el `.kicad_pcb` que está en git, no el que acaba de generarse. La
diferencia es lo que caza una pieza movida en la GUI y guardada: a partir de
ahí el fichero que va a fábrica y el script que dice cómo se colocó dejan de
ser el mismo diseño.

## La telemetría

Cinco chips, ~12 USD, sin tocar la regulación:

| Magnitud | Pieza | Dir. |
|---|---|---|
| Tensión + corriente de +12 V | `U8` INA226 | 0x40 |
| Tensión + corriente del +5 V de `U3` | `U9` INA226 | 0x41 |
| −12 V, VRAW+ y VRAW− (solo tensión) | `U10` ADS1115 | 0x49 |
| Temperatura del aire del recinto | `U11` TMP1075 | 0x48 |
| Barrera GNDA / GNDD | `U12` ISO1541 | — |

Tres cosas que no son obvias y que decidieron el diseño:

**El valle de VRAW es el número que compra este chip.** Es contra el que se
pelearon los 9400 µF, el toroide de 120 VA y los 13,6 V de `U1`, y hasta ahora
sólo existía simulado.

**El +5 V se mide por su tensión más que por su corriente.** Ese nodo es la
*referencia* de los divisores de los canales negativos, así que medirlo hace que
la lectura de −12 V se autocalibre contra el mismo riel del que cuelga su
divisor.

**El riel negativo no lleva corriente porque no puede.** El modo común de entrada
del INA226 tiene mínimo garantizado −0,3 V (TI SBOS547C p.4): a −12 V está 40
veces fuera. Medirlo exigiría un dominio aislado entero. No es una comodidad que
se dejó fuera, es un máximo absoluto.

### El divisor

Los tres canales comparten **dos valores** al 0,1 %: 100 k y 20 k, atenuación
**1/6** en los tres. El 1/6 no es redondo por gusto — es el que hace que el pin
del ADC llegue a 0,000 V justo cuando VRAW− llega a −25 V, la tensión nominal de
los propios condensadores de bulk. **La cadena de medida no falla antes que la
pieza que mide.**

> **Invariante, y va en la seda:** el 100 k mira siempre al riel medido, el 20 k
> siempre a la referencia. Mal *dibujado* lo caza `check_netlist.py`; mal
> *poblado* (un 20 k en la huella del 100 k, las dos son 0805 idénticas) no lo
> caza nadie.

## Un rótulo que estuvo mal desde la v1

Al leer el netlist de esta versión salió que `J2`, el bus de ±12 V hacia los
módulos, tiene **el pin 1 en −12 V y el 4 en +12 V** — mientras el rótulo del
conector y el `bom.csv` decían `+12 / GND / GND / −12`, o sea lo contrario.

No hay fallo eléctrico: el esquemático y la bus board coinciden, y el
`check_netlist.py` de la bus board lo afirma («par 1 = franja roja = −12 V»,
«igual que J2 del módulo 1»). Lo que estaba mal era el **rótulo**, en el sitio
exacto donde más daño hace: quien montara el mazo leyendo esa columna habría
metido ±12 V al revés en los seis módulos. Corregido aquí y en `design-notes`
§10.4; la v1 y la v2 quedan congeladas con el suyo mal.

## La placa

**200 × 150, girada respecto de la v1 y la v2.** No es preferencia: el eje largo
de la PCB va a lo ancho del case, 200 mm de los 528 disponibles contra solo 150
de los 223 de fondo. Al revés no cabe.

![colocación](pcb/sam17-power-v3-3d-top.png)

Tres cosas de esta placa las decide el chasis, no el layout:

**Desaparecen los disipadores.** La v1 y la v2 reservaban 42 × 38,1 mm por cada
TO-220 para su Fischer individual. Aquí el disipador es la pared, así que esos
3 × 1600 mm² vuelven al layout — y por eso una placa más corta en un eje sigue
sobrándole sitio.

**La fila de TO-220 no se elige aquí.** Su X la declara `chasis_to220_x` /
`chasis_to220_paso` en `case/cad/params.scad`, y `build_pcb.py` **la lee de ese
fichero**. El canto de la placa y la pared son la misma cota vista desde dos
lados; copiar el número sería crear dos verdades que se separan en silencio el
día que una se mueva.

**El cuerpo de los tres cuelga fuera de la placa**, hacia la pared. Los 10 mm
entre el canto y la cara interior son el sitio del conformado de patas. Las
puertas de margen y de solape tienen esa excepción declarada: a esos tres se les
mide por los pads.

### Lo que la colocación tuvo que resolver

| | |
|---|---|
| La franja de red no cabía | El MOV mide 23,1 mm y la banda bajo la barrera tenía 18. La barrera baja de y=128 a y=121 |
| `L_SMPS` y `N_SMPS` no estaban en `NETS_RED` | Son la salida del choke hacia `J7`: **230 V igual que antes de entrar**. Sin ellas, `es_red()` las daba por SELV. Lo cazó la propia puerta de fuga midiendo 5,50 mm entre los dos pines de `CY2` — que son justo los que un Y2 existe para puentear |
| El filtro de modo común estaba al final de la fila | Y su retorno a PE es *todo el mecanismo* (§18.7: el choke sube impedancia, los Y dan el camino de vuelta). Movido junto al fusible, donde pincha `L_F`: el lazo se parte por la mitad |
| `J3` a 5,83 mm del tornillo `H3` | Ese tornillo va al chasis, o sea a PE. La fuga de 6 mm es exactamente la que hay que exigir ahí |

### La telemetría y el lazo

`revisar_diagonal()` heredada exige ≥ 80 mm entre el lazo de rectificación y la
isla ultra (mide **93**). Se le añadió un segundo umbral, ≥ 30 mm hasta la isla
de telemetría (mide **40**), y el umbral más bajo tiene motivo: la isla ultra
defiende 0,8 µVrms; la telemetría mide con 16 bits sobre 4 V de fondo de
escala, ~60 µV por cuenta. Tres órdenes de magnitud de diferencia en lo que hay
que proteger. Lo que sí comparten es la razón de estar lejos: los divisores son
de 100 k, y un nodo de alta impedancia junto a un lazo rectificador recoge por
capacidad lo que no recogería uno de baja.

### Y el invariante llegó a la seda

El README de esta versión declaraba un hueco: el divisor mal *dibujado* lo caza
`check_netlist.py`, mal *poblado* (un 20 k soldado donde va el 100 k, las dos son
0805 idénticas) no lo caza nadie. Ahora hay dos líneas de serigrafía entre las
dos filas, que es donde mira quien las suelda:

```
R21 R22 R23 = 100k (AL RIEL)
R24 R25 R26 = 20k (A LA REFERENCIA)
```

Y el aviso que la v2 no necesitaba, porque allí cada TO-220 tenía su disipador
suelto y solo `U2` pedía mica: **`TABS AISLADOS: MICA + PASADOR`**. Aquí los tres
van contra la misma pared, que además es la referencia de PE, y dos de los tres
tabs están a VRAW+ y VRAW−.

## Documentación

| Fuente | Contenido |
|---|---|
| [spec 2026-08-18](../../../docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md) | Chasis de acero, térmica y telemetría |
| [plan 2026-08-18](../../../docs/superpowers/plans/2026-08-18-fuente-v3-goat.md) | Las cinco fases |
| [notes/design-notes.md](../notes/design-notes.md) | §16.8 (protección), §16.5 (VRAW), §16.12 (+5 V) |
| [../v2/README.md](../v2/README.md) | La arquitectura de regulación, que aquí no cambia |

## Lo que falta

- **Fase C — ruteo.** La colocación está cerrada (abajo); falta rutear, DRC
  limpio y el paquete de fabricación.
- ~~**Fase D — chasis.**~~ **Cerrada.** El toroide tiene hoja del fabricante
  (Ø93 × 46, 1,20 kg) y el chasis de acero existe en `case/cad/` con sus tres
  DXF de corte y su puerta. Queda abierto solo el presupuesto de la pantalla
  electrostática, que depende de Talema.
- **Fase E — validación.** El LNA de medida (#58) y el bring-up: el valle real de
  VRAW y el número de ruido real, los dos por primera vez.
