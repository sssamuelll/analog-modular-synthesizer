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
disipación de toda la cadena de regulación cae a **~3.0 W**, y una caja cerrada
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
| Disipación | **Contra la pared del chasis**, sin disipadores discretos | Con 3.0 W de regulación el chasis sobra, y se ganan ~39 °C de unión |
| Ventilación del recinto | **Ninguna. Va cerrado** | §3.1: 7.1 °C de subida en el peor caso. Una rejilla solo dejaría entrar polvo |
| Telemetría | **INA226 ×2 + ADS1115 + TMP1075**, I²C | Corriente solo donde vale: §4.2. El ADS1115 entra por los dos VRAW, que es el número que nunca se ha medido. El TMP1075 ya se usa en el módulo 3 |
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
| **`U3` (7805)** | — | **faltaba** | **0.47 W** |
| **Regulación** | **4.80 W** | ~~1.29 W~~ | **2.99 W** |
| Núcleo del toroide | ~2 W | | **~1.6 W**, y ahora con fuente |

`U3` no estaba en las dos primeras versiones de esta tabla y es el que más
depende de una decisión, no de un cálculo: §16.12 acota su riel a **300 mA como
límite de diseño**, y a ese techo disiparía **4.66 W** — más que los dos
pre-reguladores juntos. Su carga real es otra cosa: desde el 2026-08-18 (#118)
se sabe que alimenta **solo el módulo 2**, por el conector dedicado `J6`, y no
«los DACs ×5» que decía §7 de la spec v2 — el bus SAM17 es de cuatro hilos
(+12/GND/GND/−12) y **no lleva 5 V**. Con el módulo 2 más la isla de telemetría
de §4, son ~30 mA y **0.47 W**.

> **El techo de 300 mA de §16.12 es el que rompería esta caja, no la carga.** Si
> algún día algo pide ese riel en serio, la térmica del recinto se rehace antes.


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
| LED apagados | 1.00 W | 0.28 W | **5.27 W** | **4.0 °C** |
| LED al tope del #104 (2.80 A) | 15.00 W | 4.23 W | **9.22 W** | **7.1 °C** |

Superficie del recinto propuesto (§3.3), **descontando la cara inferior**
porque apoya contra la bandeja y no convecta:

```
2(0.3386 x 0.083) + 2(0.1766 x 0.083) + 1(0.3386 x 0.1766) =  0.1453 m2
dT = 9.22 W / (0.1453 m2 x 9 W/m2K)                        =  7.1 C  (peor caso)
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
con 7.1 °C de resultado en el peor caso, tendría que estar equivocado por un
factor de cuatro para que importe.

> **Corregido el 2026-08-19.** Esta cuenta daba 7.9 °C sobre un recinto de
> 310 × 160 × 85, que era demasiado pequeño para meter el toroide al lado de la
> PCB (§3.3). Con el recinto real son **+12 % de superficie** y la subida baja de
> 7.9 a 7.1 °C. La caja crece por geometría y disipa por superficie.

> **Y otra vez el mismo día, al dibujarla.** Los 342 × 180 × 85 de la primera
> versión de §3.3 no eran una cota: eran «chapa de 1.5 mm + pestañas», una
> estimación de cuánto crece la caja alrededor de su interior. Al derivarla de
> verdad —interior 332 × 170 × 80, chapa doblada, tapa con faldón por fuera— el
> exterior sale **338.6 × 176.6 × 83**: 3.4, 3.4 y 2 mm MENOS.
>
> No cambia ninguna decisión y aun así se anota, porque la superficie es el
> denominador de esta sección: 0.1453 m² en vez de 0.1503 (−3.3 %), ΔT de 7.1 en
> vez de 6.8, y la Tj de `U2` de 61.4 en vez de 61.1 °C. Sigue redondeando a
> **61** y el margen contra los 125 no se entera.
>
> La caja sobreestimada era la conservadora en el reparto de espacio y la
> **optimista** en la térmica. Se corrigen las dos con el mismo número.

> **Los 2 W del toroide también tenían fuente ahora.** La hoja de Nuvotem da
> **0,73 W de pérdidas en hierro** (fijas, no escalan con la carga) y **15,2 W en
> cobre a plena carga**, o sea a 5 A por devanado. Al techo de diseño de la
> fuente —650 mA por riel, ~1,17 A rms por devanado con el factor de forma de un
> rectificador con filtro capacitivo— el cobre aporta 0,83 W: **1,56 W en total**,
> no 2. Al censo real (174 mA/riel) son **0,79 W**.
>
> Se deja el 2 W redondo en la suma de 9,22 W: sigue siendo el techo conservador,
> y ahora se sabe *cuánto* de conservador.

Cadena térmica del componente más caliente, `U2` (LM2991, ~1.1 W al censo real).
El chasis no se calienta solo por `U2`: lo calientan los 9.22 W de todo lo que
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
Tj = ambiente  +  subida del chasis por los 9,22 W  +  P_U2 x R_union-chasis
   = 45 C      +  7,1 C                             +  1,1 W x 8,5 K/W
   = 61 C
```

Contra los **~101 °C** que da hoy §16.7 con su Fischer individual. **39 °C de
regalo por dejar de tratar el calor como un problema de tres piezas y tratarlo
como uno de una sola.**

El eslabón débil es el extendido en acero: el acero conduce ~4× peor que el
aluminio. A 0.8 W no importa. Si al medir importara, la salida es una placa
extensora de aluminio atornillada a la pared — **no se dibuja hasta que la
medida la pida**.

#### La curva de derating, por fin leída — y el techo del #104 baja a 2.50 A

Esta cuenta tenía un cabo suelto declarado: la IRM-15-5 se especifica de −30 a
+85 °C *«refer to Derating Curve»*, y esa curva nadie la había abierto. Ya está
leída (Mean Well `IRM-15-SPEC`, 2025-11-21, p.3):

**El tramo plano del 100 % acaba en +50 °C.** De ahí baja en recta hasta el
final de la escala.

Y la caja, al tope del #104, está **a 52.7 °C por dentro**. Tres grados pasado
el codo. Lo que sigue es un lazo, no una tabla: la SMPS calienta el recinto, el
recinto la derratea, y menos capacidad no significa menos calor.

| Tope del #104 | Pide | Calor dentro | Aire dentro | Puede dar | Margen |
|---|---|---|---|---|---|
| **2.80 A** | 14.00 W | 8.94 W | 52.7 °C | 13.9 – 14.4 W | **−0.06 a +0.43 W** |
| **2.50 A** | 12.50 W | 8.52 W | 52.3 °C | 14.1 – 14.5 W | **+1.58 a +2.01 W** |

El rango sale de lo único que no se lee limpio del PDF: el codo a +50 °C es
inequívoco (el segmento plano va de −10 a 50.0 °C), pero la **pendiente** de
después depende de dónde acaba la recta, y la escala vertical de ese gráfico
tiene marcas irregulares. Se dan las dos lecturas.

**Da igual cuál sea la buena: a 2.80 A el margen es de menos del 3 %**, y esa
cifra cuelga de un coeficiente de convección estimado y de un ambiente de 45 °C
supuesto. Un margen del 3 % construido sobre dos suposiciones no es un margen.

> **El tope del #104 baja de 2.80 A a 2.50 A.**

Dos cosas honestas sobre esto:

- **A 25 °C de ambiente no pasaría nada.** El interior quedaría en 32.7 °C, por
  debajo del codo, y la SMPS daría sus 15 W enteros. Los 2.80 A funcionan en una
  habitación normal y fallan en la habitación para la que se dimensionó todo lo
  demás de este diseño. Se decide por el peor caso publicado, que es la regla de
  §16.1.
- **La tabla de arriba se queda con sus 9.22 W.** Con el tope nuevo el número
  real es 8.52 W y 6.3 °C, pero bajarlo sería cambiar un techo por otro más
  apretado. Se deja el conservador: ahora es un techo con margen en lugar de un
  techo justo.
- **La caja creció después de esta cuenta, y el veredicto no se movió.** Con el
  recinto real (§3.3, +16 % de superficie) el interior al tope viejo queda en
  51.6 °C en vez de 52.7, y el margen a 2.80 A pasa de −0.06…+0.43 W a
  +0.36…+0.66 W, o sea **2.6 % a 4.7 %**, contra el **16 %** que da 2.50 A. Sigue siendo un margen de un dígito
  sobre un coeficiente estimado y un ambiente supuesto, contra el **16 %** que da
  2.50 A. El tope se queda en 2.50 A.

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
toroide                 O93 x 46 mm      1,20 kg -- hoja del FABRICANTE
bandeja base            528,32 x 223,26 mm
alto interior inferior  125,13 mm
```

> **El toroide se corrigió dos veces el mismo día, y la segunda deshizo la
> primera.** Vale la pena dejarlo escrito, porque la moraleja pesa más que el
> número.
>
> | | fuente | Ø | alto | peso |
> |---|---|---|---|---|
> | `params.scad` original | *ninguna*, heredado (#46) | — | 45 mm | — |
> | «corrección» | dos listados **RS** del MPN | 105 mm | 52,1 mm | 1,33 kg |
> | **buena** | **hoja Nuvotem `RS0120P1-2-012`** | **93 mm** | **46 mm** | **1,20 kg** |
>
> Los 45 originales estaban **a 1 mm de la verdad**. La corrección intermedia se
> fue 6 mm en el otro sentido, apoyada en dos fuentes coincidentes que eran las
> dos secundarias. **La regla de §16.1 —fuente primaria, no agregador— no es solo
> para límites de seguridad**: aquí costó una geometría de chasis entera.
>
> El **+4 mm al diámetro sí se mantiene**, porque lo dice la propia hoja:
> *«Measured away from leadout bulge; allow extra 4mm at leads»*. Envolvente de
> diseño **Ø97**.
>
> Sigue habiendo que **medir la pieza al recibirla**. El peso, de paso, cierra la
> estimación de masa del #106, y el kit de montaje resulta ser **perno M6×60 con
> dos discos de neopreno y arandela cóncava** — dato que la Task 9 necesita.

La PCB va con su **eje largo a lo ancho del case**: 200 mm de los 528
disponibles, contra solo 150 de los 223 de fondo. Al revés no cabe — 200 mm de
PCB en 223 mm de bandeja deja 23 mm para paredes, cables y tolerancia, que no
es margen sino suerte.

Recinto resultante. Los 300 × 150 provisionales **no cerraban**: 200 mm de PCB
más 109 de toroide son 309 antes de tocar una holgura, y los 150 de fondo eran
exactamente el fondo de la PCB, o sea cero holgura contra las paredes.

```
                 10 + 200 + 15 + 97 + 10
interior   332   x 170   x 80  mm   pared, PCB, cableado, toroide, pared
exterior   338,6 x 176,6 x 83  mm   DERIVADO (ver abajo), no estimado
sobra      189,7 mm de largo y 46,7 de fondo en la bandeja de 528,32 x 223,26
           32,1 mm de alto sobre la caja y sus pies, en los 125,13 del piso
```

> **El exterior dejó de ser una estimación el 2026-08-19**, al dibujar la caja
> (plan Task 9). Aquí decía *342 × 180 × 85, «chapa de 1.5 mm + pestañas»*, que
> es una forma de decir «el interior más un poco». La caja real se deriva del
> interior, del espesor y del faldón de la tapa, y sale **3,4 / 3,4 / 2 mm más
> chica**. La consecuencia está en §3.1: menos superficie, ΔT de 7,1 y no 6,8.

**Crecer resultó ser buena noticia.** La superficie de convección sube de
0,1295 a **0,1453 m²** (+12 %), así que la caja disipa mejor de lo que decía
§3.1 — ver la corrección ahí mismo.

El recorte de **104 × 32 mm** que la bandeja ya llevaba cortado bajo el PSU
(`bandeja_base_2d`) **deja de ser ventilación**: pasa a ser la salida de cables
del recinto hacia el interior del case. Y al dibujarlo salieron dos cosas que
el párrafo anterior daba por hechas y no lo eran:

- **Aquello no era un agujero.** Era un campo de ondas —ranuras de 4 mm con
  puentes entre ellas— cuya *envolvente* mide 104 × 32. Por 4 mm no pasa un
  mazo. Ahora es una abertura de verdad, y se deriva de la ranura del suelo del
  chasis con una sola función, así que la contiene por construcción.
- **La salida no cabe en el hueco de cableado.** Los 15 mm entre PCB y toroide
  no dan para una ranura de 26, y correrla hacia el toroide la mete debajo de
  él —lo cazó el propio gate al primer intento—. Así que **el mazo sale por
  debajo de la PCB**, por el hueco de sus separadores de 10 mm. Eso es una
  condición para la Task 6: `J2` y `J6` miran a ese canto.

## 4. La telemetría

### 4.1 Qué se mide, y en qué dirección

| Magnitud | Pieza | Dir. | Por qué esa |
|---|---|---|---|
| Tensión + corriente de +12 V | INA226 (`U8`) | 0x40 | 16 bits, las dos medidas en un chip, y su modo común llega a 40 V |
| Tensión + corriente del +5 V de `U3` | INA226 (`U9`) | 0x41 | su **tensión** es la referencia de los canales negativos — §4.4 |
| Tensión de −12 V (**solo tensión**) | ADS1115 `AIN0` (`U10`) | 0x49 | §4.2 |
| **Valle de VRAW+ y VRAW−** | ADS1115 `AIN1` y `AIN2` | 0x49 | el número contra el que se pelearon los 9400 µF, el toroide de 120 VA y los 13.6 V de `U1` — y que hasta hoy **solo existe simulado** |
| Temperatura del aire del recinto | TMP1075 (`U11`) | 0x48 | **ya se usa en el módulo 3**, con los mismos straps: driver escrito |

`AIN3` se queda sin usar, atado a GNDA — el datasheet lo permite explícitamente
(TI SBAS444E §9.1.4), así que no lleva ni puente ni huella.

Cinco chips, ~12 USD, sin tocar la topología de regulación. Se alimentan del
+5 V de `U3`, que es lineal y está en GNDA — el dominio correcto para medir los
rieles analógicos (§3.1).

Dos correcciones que salieron al escribir el `bom.csv` y que la primera versión
de esta tabla tenía mal:

- **El TMP1075 se queda en 0x48 y el ADS1115 se mueve a 0x49**, no al revés. Con
  `ADDR` a GND el ADS1115 también responde en 0x48 y **chocaba con el sensor**.
  Se mueve el ADC porque el sensor en 0x48 conserva exactamente los straps del
  `U13` del módulo 3, y con ellos el driver ya escrito.
- **El +5 V que se mide es el de `U3`, no el de la SMPS.** El árbitro de LEDs del
  #104 vive en el +5 V digital, y ese riel **no pasa por esta placa**: la
  IRM-15-5 se monta fuera y su salida va directa al lado digital (spec v2 §7).
  Medir sus 2.80 A es trabajo del módulo 2, no de aquí.

### 4.2 El riel negativo: no es que sea difícil, es que no se puede

Un INA226 mide un shunt referido cerca de su propia alimentación, y el datasheet
pone el número: **modo común de entrada de −0.3 V a 40 V** (TI SBOS547C, p.4,
tabla 5.1). Un shunt en el riel de −12 V lo pone a −12 V de modo común, o sea
**40 veces fuera de su mínimo garantizado**. No es una incomodidad de diseño: es
un máximo absoluto.

**Así que el riel negativo lleva solo tensión**, por divisor a referencia
positiva leído por el ADS1115. Y la decisión sobrevive por valor además de por
física: de las cuatro medidas, la corriente del riel negativo es la menos útil
—el autoafinado quiere *tensión*, el árbitro del #104 vive en el +5 V, y los PTC
de la bus board son por módulo, no por riel.

> **Cambio respecto del plan: NO va huella de shunt de 0 Ω en −12 V.**
>
> El plan la dejaba «por si el bring-up pide esa corriente». Con el número del
> datasheet delante, esa huella no habilita nada: para medirla haría falta un
> segundo dominio aislado entero, con su propia alimentación y su propio
> aislador. Eso es un diseño, no una resistencia. Y mientras tanto sería una
> junta de soldadura más en serie con un riel de potencia, comprada a cambio de
> nada.
>
> El constraint de «lo que no se decide sale con huella y DNP» es para lo que
> queda **abierto**. Esto no quedó abierto: lo cerró un máximo absoluto.

### 4.3 El cruce de masas: aislado

La telemetría nace en el dominio analógico de la fuente; el RP2350 vive en
GNDD. `architecture-poly.md` §7 ya fijó la regla de aislamiento de GNDD para
los WS2812, y esto es el mismo problema.

**ISO1541** (aislador de I²C bidireccional, sin control de dirección). Un chip,
~3 USD. La alternativa —un solo punto de unión— es defendible porque los dos
dominios comparten transformador, pero el riesgo es que el reloj del I²C se
acople al riel justo donde el LT3045 estaba comprando microvoltios. En una
fuente cuya razón de existir es el ruido, esa apuesta no se hace por 3 USD.

Los dos lados van a tensiones distintas —**lado 1 a 3.3 V** (el dominio del
RP2350), **lado 2 a 5.0 V** (el analógico)— y eso no es un apaño: el chip admite
3.0 a 5.5 V por lado, independientes (TI SLLSEB6F, p.1). El plano de masa no
cruza la barrera.

Los pull-ups del lado GNDA van en esta placa (`R27`/`R28`, 2.2 k). Los del lado
GNDD **van con huella y DNP** (`R29`/`R30`): el módulo 2 todavía no está
diseñado (#111) y no se sabe si los lleva. Son **mutuamente excluyentes** —
poblar las dos parejas da 1.1 k en paralelo, 3 mA, y el lado 1 solo sumidera
3.5 mA especificados.

**El conector de ese bus, `J8`, es JST-PH de 2.00 mm a propósito.** `J2` (el bus
de ±12 V) y `J6` (+5 V) son KK-254 de 2.54 mm: con este paso, el cable del I²C
**no cabe** en ninguno de los dos. Un cable de I²C enchufado en el bus de ±12 V
mata el RP2350 y los cuatro chips de la isla a la vez, y la única protección que
de verdad funciona contra eso es geométrica.

> **Enmienda del 2026-08-30 (D1):** el micro de esta sección es hoy el
> **STM32N657**, no el RP2350 (spec del hub N657, D1). No cambia nada de la
> doctrina: el lado 1 del ISO1541 sigue a 3.3 V en GNDD, el J8 sigue siendo
> JST-PH de 2.00 mm para que el cable del I²C no entre en el bus de ±12 V,
> y un error de cableado ahí sigue matando el micro del módulo 2 y los
> cuatro chips de la isla.

El bus entra al mux I²C que `architecture-poly.md` §8 ya tiene previsto por las
EEPROM de identidad, que responden todas en 0x50. La fuente toma un canal, y
dentro de ese canal 0x40, 0x41, 0x48 y 0x49 no chocan ni entre sí ni con 0x50.

### 4.4 Los divisores: dos valores, tres canales, un solo número

Los tres canales del ADS1115 usan **las mismas dos resistencias al 0.1 %**:
100 k y 20 k. Con eso la atenuación es **1/6 exacta**, igual en los tres, y el
firmware queda con una sola pendiente:

```
canal positivo   tap = VRAW+ / 6                     (referencia = GNDA)
canales negativos tap = V5 x 5/6  +  V_riel / 6      (referencia = +5 V)
```

El offset de los canales negativos es `V5 x 5/6`, y **`V5` es justo lo que mide
`U9`**. La lectura de −12 V se autocalibra contra el mismo riel del que cuelga
su divisor: eso es lo que compra el INA226 del +5 V, más que su corriente.

**El 1/6 no es un número redondo por gusto.** Es el que hace que el pin del ADC
llegue a 0.000 V exactamente cuando VRAW− llega a −25 V, o sea a la tensión
nominal de los propios condensadores de bulk:

| Riel | Pin del ADC |
|---|---|
| VRAW+ a +20.54 V (peor caso publicado) | +3.423 V |
| VRAW+ al límite de 25 V del bulk | +4.167 V |
| −12 V nominal | +2.167 V |
| −12.9 V (post-regulador en corto) | +2.017 V |
| VRAW− a −20.54 V | +0.743 V |
| VRAW− al límite de 25 V del bulk | **0.000 V** |

**La cadena de medida no falla antes que la pieza que mide.** La ventana del
chip es GND−0.3 V a VDD+0.3 V (TI SBAS444E, p.4), y ningún estado físicamente
alcanzable de esta fuente la saca de ahí.

Dos cosas más que van con esto:

- **Invariante:** el 100 k mira siempre al riel medido, el 20 k siempre a la
  referencia. Cambiarlos de sitio deja de atenuar y mete el riel entero en un
  pin de 5.3 V de máximo absoluto. Tiene **dos guardianes distintos**: si está
  mal *dibujado* lo caza `kicad/check_netlist.py` contra el netlist real; si
  está bien dibujado y mal *poblado* —un 20 k soldado en la huella del 100 k,
  las dos son 0805 idénticos— no lo caza ninguna puerta, y por eso va además en
  la **seda de la placa**. Ese hueco queda declarado, no tapado.
- **Dos clamps Schottky** (`D14`, `D15`) en los taps negativos. No están por
  supervivencia —los 100 k limitan a 126 µA, 79 veces por debajo del límite de
  10 mA que TI publica para eso mismo (§9.1.3)— sino por esto, textual del
  §7.3.1: *sobreexcitar una entrada del ADS1115 altera las conversiones de las
  otras*. Sin diodo, un fallo del +5 V le quita la razón a las tres medidas a la
  vez, justo cuando hacen falta para diagnosticarlo.

Toda esta aritmética vive como puerta ejecutable en
`hardware/01-power-supply/v3/check_telemetria.py`, con la cita de página al lado
de cada límite.

## 5. Lo que compra

Esto no es «ahora hay datos». Son cuatro cosas medibles:

1. **El autoafinado puede ATRIBUIR la deriva.** Hoy mide frecuencia y corrige.
   Con la tensión del riel distingue *«derivó el oscilador»* de *«se hundió la
   fuente»*, y solo quema calibración en el primero.
2. **El #104 deja de ser a ciegas — pero no desde aquí.** Ese árbitro de
   corriente de los LED se escribió estimando-antes-de-encender porque no había
   forma de medir. La medida existe ahora, y va en el módulo 2: el +5 V digital
   **no pasa por esta placa** (§4.1). Lo que sí llega desde aquí es su
   *consecuencia* — el `TMP1075` mide el aire que calientan los 4.23 W que
   pierde la SMPS al tope de 2.80 A, así que ese tope deja de ser una fila de
   tabla y pasa a ser algo que la caja reporta.
3. **Los 12 PTC de la bus board dejan de ser invisibles.** Hoy un módulo que se
   acerca a sus 250 mA de hold no avisa; se entera cuando dispara.
4. **El farol (#42) puede mostrar salud, no solo color.** Que es la versión
   honesta de «el instrumento se conoce a sí mismo».

## 6. Lo que NO está confirmado

- ~~**El diámetro del toroide**~~ — **resuelto a medias el 2026-08-19.** El
  catálogo del MPN real (Nuvotem Talema 0120P1-2-012) da **Ø105 × 52,1 mm y
  1,33 kg**, y los tres están ya en `params.scad`. Los 45 mm de alto que había
  eran 7,1 mm menos que la pieza. **Sigue siendo catálogo de distribuidor y sigue
  habiendo que medir la pieza al recibirla** — pero §3.3 ya no es provisional
  sobre una cifra sin fuente, es provisional sobre una con procedencia.
- **La pantalla electrostática del toroide, y es la única decisión de esta spec
  con fecha límite.** `design-notes` §18.7 (nueva) desarrolla el camino: la SMPS
  inyecta modo común en la red, la capacidad entre devanados del toroide lo cruza
  al secundario, y **el PSRR no lo rechaza porque no llega como variación de
  alimentación sino como corriente por la masa**. El dato que decide es que la
  IRM-15 conmuta a **65 kHz** y la emisión conducida de EN 55032 **empieza a
  medir en 150 kHz**: su certificado de clase B no dice nada del fundamental ni
  del segundo armónico. La pantalla va dentro del bobinado — o se pide así o no
  se pone nunca. Y en Talema no es un sufijo de catálogo sino un *special*.
  **Falta la magnitud**: nadie publica el modo común de la IRM-15 bajo 150 kHz ni
  la capacidad entre devanados del toroide, así que §18.7 establece un mecanismo
  y un plazo, no una cifra.
- **R_thJC del LM2991 en TO-220-5** — se toma ~3 K/W de catálogo. Puerta de
  datasheet antes de congelar, misma disciplina que §16.1 (garantizado ≠ típico).
- **El extendido térmico en chapa de acero** (~4 K/W) es una estimación. Es el
  eslabón débil de la cadena y el único candidato a placa extensora de aluminio.
- **El espesor de chapa.** 1.5 mm es supuesto; lo decide el taller de doblado
  junto con los radios de plegado.
- ~~**La protección de sobretensión está en revisión** (#114)~~ — **cerrado el
  2026-08-18.** §16.8 se reescribió contra el BOM real y salieron dos cosas: la
  cascada de dos etapas de la v2 ya protege sola (ningún fallo simple pone más
  de ±13.1 V en el bus, y los LT3045/LT3094 aguantan VRAW con 1.46 V de margen),
  y el lazo del crowbar **no cerraba con ningún SCR** porque `F1` a 1.6 A no
  está obligado a abrir a los 2.79 A que refleja el fallo. **La v3 no lleva
  crowbar en ningún riel** (#118). Lo que sí queda dentro de esta caja por eso:
  el requisito de fusible térmico en TR1.
- ~~**La curva de derating de la IRM-15-5**~~ — **leída el 2026-08-19** (Mean
  Well `IRM-15-SPEC`, 2025-11-21, p.3). El codo está en **+50 °C** y la caja al
  tope viejo quedaba en 52.7 °C: el tope del #104 baja a **2.50 A**. Ver §3.1.
  Lo que queda sin confirmar de ahí es solo la **pendiente** después del codo, y
  la decisión no depende de ella.
- ~~**Si TR1 trae fusible térmico embebido**~~ — dejó de ser una duda: en el
  `bom.csv` de la v3 es **criterio de aceptación**. Un TR1 sin él no se compra.
  Los 642 W de cualquier corto del secundario son la cuenta que ni `F1` ni un
  crowbar cubren (#118), y esto pasa dentro de un recinto cerrado.
- **El +5 V de la isla cuelga de un solo 7805.** `U3` en corto pone los 20.54 V
  de VRAW+ en un nodo del que dependen cinco chips de 6 V de máximo absoluto
  **y** el módulo 2 por `J6`. El riesgo ya existía para el módulo 2; la
  telemetría le pone más detrás. Y no se arregla con un clamp: un clamp sin nada
  que abra el circuito es exactamente el error del crowbar otra vez. Queda
  abierto a propósito, no resuelto a medias.

## 7. Verificación

| Qué | Cómo | Cierra |
|---|---|---|
| La caja no se calienta | Termopar en la pared tras 2 h, **con los LED al tope del #104** (que es quien manda la pérdida de la SMPS). Se esperan < 10 °C sobre ambiente | §3.1 |
| Ningún tab toca el chasis | Ohmímetro entre cada tab y el chasis, con la placa desconectada. Se espera circuito abierto | §3.2 |
| El PE llega a todo metal accesible | Ohmímetro entre la clavija de tierra y el chasis. Se esperan miliohmios (§13.4) | #107, #47 |
| La telemetría concuerda | Comparar la lectura de cada INA contra el multímetro en TP1-TP6 | §4 |
| **Los divisores atenúan lo que dicen** | Multímetro en TP9-TP11 (los taps) contra TP1/TP2/TP4 (los rieles): se espera 1/6 dentro del 0.2 %. Con las tres medidas —riel, tap y código I²C— se sabe **cuál** eslabón está mal; con dos solo que algo no cuadra | §4.4 |
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
