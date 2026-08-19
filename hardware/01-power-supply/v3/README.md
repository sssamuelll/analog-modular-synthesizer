# PSU v3 — la primera que se construye

**Estado:** Fase A cerrada (decisiones), Fase B cerrada (esquemático). Faltan
PCB, chasis y validación.

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

Las dos últimas se reparten un hueco a propósito: `check_bom.py` pasaría en verde
con SDA y SCL cambiados —no falta ni sobra un componente, sobra un cable en el
sitio equivocado— y por eso existe la de netlist.

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

## Documentación

| Fuente | Contenido |
|---|---|
| [spec 2026-08-18](../../../docs/superpowers/specs/2026-08-18-fuente-chasis-telemetria.md) | Chasis de acero, térmica y telemetría |
| [plan 2026-08-18](../../../docs/superpowers/plans/2026-08-18-fuente-v3-goat.md) | Las cinco fases |
| [notes/design-notes.md](../notes/design-notes.md) | §16.8 (protección), §16.5 (VRAW), §16.12 (+5 V) |
| [../v2/README.md](../v2/README.md) | La arquitectura de regulación, que aquí no cambia |

## Lo que falta

- **Fase C — PCB.** Colocación de los tres TO-220 en fila con los tabs
  coplanares, y la puerta `test_to220_coplanares` que lo mide. Se cierra con la
  Fase D o no se cierra.
- **Fase D — chasis.** Medir el toroide de verdad (el diámetro ni siquiera está
  en `params.scad`, #46) y el chasis paramétrico en `case/cad/`.
- **Fase E — validación.** El LNA de medida (#58) y el bring-up: el valle real de
  VRAW y el número de ruido real, los dos por primera vez.
