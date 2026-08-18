# Fuente v2 — chasis de acero y telemetría

**Fecha:** 2026-08-18 · **Estado:** diseño acordado con Samuel, pendiente de
plan de implementación · **Se apoya en:**
[spec fuente v2 «GOAT»](2026-08-16-psu-v2-goat-design.md), que fija la
topología de regulación y no se toca aquí.

## 1. Objetivo, y por qué esto se pudo recién hoy

Dos cosas que hasta esta mañana no se podían pedir juntas:

1. **Que la fuente tenga chasis.** `design-notes.md` §13.3 exige un espárrago
   de PE «soldado o remachado al chasis» desde que el cajón era de madera. El
   cajón es de acrílico desde la rev. 2 y **el chasis nunca existió** (issue
   #107). Es un hueco de seguridad, no un acabado.
2. **Que la fuente se sepa a sí misma.** El §1 de la spec v2 dice que el
   autoafinado cronometra contra referencias que cuelgan de estos rieles y que
   cualquier deriva del riel se convierte en cents. Y sin embargo la fuente no
   tiene un solo sensor: dos LED de presencia y seis test points.

Lo que cambió hoy es el **censo** (#70, cerrado): el instrumento pide
**174 mA/riel** con margen, no los 650 del punto de diseño. Con eso la
disipación de toda la cadena de regulación cae a **~2.5 W**, y una caja cerrada
deja de ser un horno. Antes del censo, el #107 se escribió con los reguladores
FUERA precisamente por eso.

**El margen no se puede devolver.** §16.4 de `design-notes.md` eligió el
toroidal de 120 VA por resistencia de devanado (0.28 Ω), no por capacidad: con
uno menor el valle de VRAW cae por debajo de los 13.6 V que exige el
pre-regulador y la fuente deja de regular. Así que la holgura térmica es una
consecuencia estructural, y la única pregunta es en qué se gasta.

Se gasta en esto.

## 2. Decisiones fijadas (con Samuel, 2026-08-18)

| Decisión | Elección | Por qué |
|---|---|---|
| Material del chasis | **Acero**, no aluminio | El aluminio es casi transparente al campo magnético de 50/100 Hz; el ferromagnético no. Decidido en #107 |
| Alcance del recinto | **Toda la fuente adentro**: toroide + PCB completa + entrada IEC | La red no sale nunca del recinto. Es lo que hacen las fuentes profesionales y es lo que da la regla del §3.2 |
| Disipación | **Contra la pared del chasis**, sin disipadores discretos | Con 2.5 W de regulación el chasis sobra, y se ganan ~39 °C de unión |
| Ventilación del recinto | **Ninguna. Va cerrado** | §3.1: 7.5 °C de subida en el peor caso. Una rejilla solo dejaría entrar polvo |
| Telemetría | **INA226 ×3 + TMP1075**, I²C | Tensión y corriente por riel con un chip; el TMP1075 ya se usa en el módulo 3 |
| Cruce de masas | **Aislado, ISO1541** | En una fuente cuyo objetivo entero es sub-µV, meterle un bus digital sin aislar deshace el diseño |

## 3. El chasis

### 3.1 Térmica: por qué va cerrado

Contenido térmico del recinto, al censo real (174 mA/riel), escalado desde la
tabla del §4 de la spec v2 (que está a 650 mA):

**La disipación NO escala con la corriente.** Cuando baja la carga, el riel
crudo *sube* porque hay menos caída en la resistencia del devanado, así que el
regulador quema más voltios por amperio. Escalar linealmente da la mitad del
número real.

```
sin carga    VRAW = 20,54 V                       (§16.5)
a 650 mA     VRAW = 15,70 V   -> caida de 4,84 V  (§4 de la spec v2)
a 174 mA     VRAW ~ 19,24 V   -> caida de 1,30 V  (proporcional a la carga)
```

| Elemento | a 650 mA | a 174 mA, mal (lineal) | a 174 mA, **bien** |
|---|---|---|---|
| LM2941 | 1.70 W | ~~0.46 W~~ | **1.07 W** |
| LM2991 | 1.80 W | ~~0.48 W~~ | **1.10 W** |
| LT3045 ×2 | 0.72 W | 0.19 W | 0.19 W |
| LT3094 ×2 | 0.58 W | 0.16 W | 0.16 W |
| **Regulación** | **4.80 W** | ~~1.29 W~~ | **2.52 W** |
| Núcleo del toroide | ~2 W | | ~2 W (no escala con carga) |

Y de ahí sale un corolario que conviene dejar escrito, porque contradice la
intuición: con `P(I) = (20.54 − 7.45·I − 13.1)·I`, la disipación del
pre-regulador **tiene máximo en I ≈ 0.50 A**, no a plena carga.

> **El peor caso térmico de esta fuente no está a 650 mA. Está a media carga.**

Los 650 mA del punto de diseño ya van pasado el pico, y los 174 mA reales están
holgadamente por debajo.

A eso hay que sumarle **la SMPS del +5 V digital**, que también vive dentro
porque se alimenta de red. La IRM-15-5 rinde **78 %** (Mean Well, tabla de
especificaciones), y su pérdida **no es constante: la manda el brillo de los
LED**, que están fuera de la caja pero cuelgan de ella.

| Estado | Salida | Pérdida IRM-15-5 | Total dentro | ΔT |
|---|---|---|---|---|
| LED apagados | 1.00 W | 0.28 W | **4.80 W** | **4.1 °C** |
| LED al tope del #104 (2.80 A) | 15.00 W | 4.23 W | **8.75 W** | **7.5 °C** |

Superficie del recinto propuesto (§3.3), **descontando la cara inferior**
porque apoya contra la bandeja y no convecta:

```
2(0.310 x 0.085) + 2(0.160 x 0.085) + 1(0.310 x 0.160)  =  0.1295 m2
dT = 8.75 W / (0.1295 m2 x 9 W/m2K)                     =  7.5 C   (peor caso)
```

**El presupuesto de brillo del #104 es también el termostato de esta caja.**
Ninguno de los dos documentos lo sabía: el #104 se escribió pensando solo en
que el riel no se hundiera, y la primera versión de esta sección olvidó contar
la SMPS. Son el mismo número visto desde dos lados.

Y sale un dato que el #104 necesita: al tope de 2.80 A la IRM-15-5 entrega
**15.0 W de sus 15 W nominales — el 100 % de su capacidad**, dentro de un
recinto cerrado. El árbitro no solo evita un brownout; es lo único que impide
que una fuente de 15 W corra a 15 W de forma sostenida ahí dentro.

El rendimiento a carga parcial es peor que el nominal, así que la fila de «LED
apagados» es optimista. No cambia nada: el peor caso ya está calculado arriba.

El coeficiente de 9 W/m²K es el valor de manual para convección natural en aire
quieto sobre superficie pintada. **Es una estimación, no una medida** — pero
con 7.5 °C de resultado en el peor caso, tendría que estar equivocado por un
factor de cuatro para que importe.

Cadena térmica del componente más caliente, `U2` (LM2991, ~1.1 W al censo real).
El chasis no se calienta solo por `U2`: lo calientan los 8.75 W de todo lo que
hay dentro. Así que la cuenta va en dos tramos y **no** en una sola cadena —
primero cuánto sube el chasis por el total, y encima cuánto sube la unión por
su propia potencia.

| Tramo | K/W | Procedencia |
|---|---|---|
| R_thJC TO-220-5 | ~3 | datasheet, **a confirmar** |
| Aislante (mica + grasa o silpad) | ~1.5 | catálogo típico |
| Extendido en chapa de acero 1.5 mm | ~4 | **estimado — el eslabón débil** |
| **Unión a chasis** | **~8.5** | los tres de arriba |

```
Tj = ambiente  +  subida del chasis por los 8,75 W  +  P_U2 x R_union-chasis
   = 45 C      +  7,5 C                             +  1,1 W x 8,5 K/W
   = 62 C
```

Contra los **~101 °C** que da hoy §16.7 con su Fischer individual. **39 °C de
regalo por dejar de tratar el calor como un problema de tres piezas y tratarlo
como uno de una sola.**

El eslabón débil es el extendido en acero: el acero conduce ~4× peor que el
aluminio. A 0.8 W no importa. Si al medir importara, la salida es una placa
extensora de aluminio atornillada a la pared — **no se dibuja hasta que la
medida la pida**.

### 3.2 La regla: el chasis conduce calor, nunca corriente

Los tres reguladores tienen el tab conectado a algo, y la caja está bondada a
tierra de protección:

| | tab a | atornillado desnudo daría |
|---|---|---|
| `U1` LM2941 | GND | masa de señal atada a PE por el tornillo |
| `U2` LM2991 | **VIN, hasta −20 V** | **corto franco por el conductor de seguridad** |
| `U3` 7805 | GND | igual que `U1` |

`U2` es innegociable. `U1` y `U3` son peores de lo que parecen: crean un camino
de masa que nadie diseñó, en la placa que persigue microvoltios.

> **Los tres van aislados. Lo único que toca el chasis eléctricamente es el
> espárrago de PE.**

Esto además cierra el §13.3 de `design-notes.md` tal como estaba escrito: el
espárrago por fin tiene dónde ir.

### 3.3 Geometría

Contenido y hueco disponible, medidos:

```
PCB de la fuente        150 x 200 mm     (Edge.Cuts de sam17-power-v2)
toroide                 ~O100 x 45 mm    (45 de catalogo, sin confirmar - #46)
bandeja base            528,32 x 223,26 mm
alto interior inferior  125,13 mm
```

La PCB va con su **eje largo a lo ancho del case**: 200 mm de los 528
disponibles, contra solo 150 de los 223 de fondo. Al revés no cabe — 200 mm de
PCB en 223 mm de bandeja deja 23 mm para paredes, cables y tolerancia, que no
es margen sino suerte.

Recinto resultante, **provisional hasta confirmar el diámetro del toroide**:

```
interior   ~300 x 150 x 80 mm     PCB + toroide al lado, holgura de cableado
exterior   ~310 x 160 x 85 mm     chapa de 1.5 mm + pestanas
sobra      40 mm de alto sobre la caja, dentro de los 125,13 del piso
```

El recorte de ventilación de **104 × 32 mm** que la bandeja ya lleva cortado
bajo el PSU (`bandeja_base_2d`) **deja de ser ventilación**: pasa a ser la
salida de cables del recinto hacia el interior del case.

## 4. La telemetría

### 4.1 Qué se mide

| Magnitud | Pieza | Por qué esa |
|---|---|---|
| Tensión + corriente de +12 V | INA226 | 16 bits, las dos medidas en un chip |
| Tensión + corriente de −12 V | INA226 | ver §4.2 |
| Tensión + corriente de +5 V | INA226 | cierra el lazo abierto del #104 |
| Temperatura del recinto | TMP1075 | **ya se usa en el módulo 3** — pieza conocida, driver escrito |

Cuatro chips, ~8 USD, sin tocar la topología de regulación.

### 4.2 El riel negativo es el único punto difícil

Un INA226 mide un shunt referido cerca de su propia alimentación. En −12 V no
se enchufa y ya. La salida limpia es poner el shunt **en el retorno del riel
negativo**, donde el nodo de sensado se queda pegado a masa y el INA trabaja en
su rango normal.

Eso hay que dibujarlo a propósito. **El modo de fallo es descubrirlo soldando.**

### 4.3 El cruce de masas: aislado

La telemetría nace en el dominio analógico de la fuente; el RP2350 vive en
GNDD. `architecture-poly.md` §7 ya fijó la regla de aislamiento de GNDD para
los WS2812, y esto es el mismo problema.

**ISO1541** (aislador de I²C bidireccional, sin control de dirección). Un chip,
~3 USD. La alternativa —un solo punto de unión— es defendible porque los dos
dominios comparten transformador, pero el riesgo es que el reloj del I²C se
acople al riel justo donde el LT3045 estaba comprando microvoltios. En una
fuente cuya razón de existir es el ruido, esa apuesta no se hace por 3 USD.

El bus entra al mux I²C que `architecture-poly.md` §8 ya tiene previsto por las
EEPROM de identidad, que responden todas en 0x50. La fuente toma un canal.

## 5. Lo que compra

Esto no es «ahora hay datos». Son cuatro cosas medibles:

1. **El autoafinado puede ATRIBUIR la deriva.** Hoy mide frecuencia y corrige.
   Con la tensión del riel distingue *«derivó el oscilador»* de *«se hundió la
   fuente»*, y solo quema calibración en el primero.
2. **El #104 deja de ser a ciegas.** Ese árbitro de corriente de los LED se
   escribió con un mecanismo de estimar-antes-de-encender porque no había forma
   de medir. Con un INA en el +5 V, se mide: el diseño se **simplifica**.
3. **Los 12 PTC de la bus board dejan de ser invisibles.** Hoy un módulo que se
   acerca a sus 250 mA de hold no avisa; se entera cuando dispara.
4. **El farol (#42) puede mostrar salud, no solo color.** Que es la versión
   honesta de «el instrumento se conoce a sí mismo».

## 6. Lo que NO está confirmado

- **El diámetro del toroide.** `alto_transformador = 45` es de catálogo y ya
  estaba señalado como no confirmado (#46). El diámetro ni siquiera está en
  `params.scad`. **Toda la §3.3 es provisional hasta medir la pieza física.**
- **R_thJC del LM2991 en TO-220-5** — se toma ~3 K/W de catálogo. Puerta de
  datasheet antes de congelar, misma disciplina que §16.1 (garantizado ≠ típico).
- **El extendido térmico en chapa de acero** (~4 K/W) es una estimación. Es el
  eslabón débil de la cadena y el único candidato a placa extensora de aluminio.
- **El espesor de chapa.** 1.5 mm es supuesto; lo decide el taller de doblado
  junto con los radios de plegado.
- **La protección de sobretensión está en revisión** (#114): §16.8 de
  `design-notes.md` razona contra el AS3340 y el instrumento lleva SSI2130.
  No afecta a la térmica ni a la geometría de aquí, pero sí a qué va dentro
  de esta caja.
- **La curva de derating de la IRM-15-5.** Su rango es −30 a +85 °C «refer to Derating Curve», y esa curva no se ha leído. Al tope del #104 la SMPS entrega el **100 % de sus 15 W** dentro de un recinto cerrado: hay que confirmar dónde está el codo antes de dar por bueno ese tope.
- **Si TR1 trae fusible térmico embebido** — ya pedido como ítem de compra en
  el BOM v2. Dentro de un recinto cerrado esa segunda línea de protección pesa
  más que antes.

## 7. Verificación

| Qué | Cómo | Cierra |
|---|---|---|
| La caja no se calienta | Termopar en la pared tras 2 h, **con los LED al tope del #104** (que es quien manda la pérdida de la SMPS). Se esperan < 10 °C sobre ambiente | §3.1 |
| Ningún tab toca el chasis | Ohmímetro entre cada tab y el chasis, con la placa desconectada. Se espera circuito abierto | §3.2 |
| El PE llega a todo metal accesible | Ohmímetro entre la clavija de tierra y el chasis. Se esperan miliohmios (§13.4) | #107, #47 |
| La telemetría concuerda | Comparar la lectura de cada INA contra el multímetro en los test points TP1-TP6 | §4 |
| El aislamiento sirve | Medir ruido de salida con el LNA (#58) con el I²C corriendo y en silencio | §4.3 |
| El valle es el simulado | Leer VRAW con la telemetría a carga real y comparar contra los 14.12 V de §16.5 | §16.5 |

Esa última fila es la que más vale: **el valle es el número contra el que se
pelearon todas las decisiones grandes de la fuente, y hasta ahora solo existía
simulado.**

## 8. Fuera de alcance

- La topología de regulación no se toca. Es la spec v2 y está cerrada.
- El firmware de la telemetría (driver, cadencia de muestreo, qué hace el
  autoafinado con el dato) es del lado digital — epic #29.
- La elección de taller de doblado y el precio.
