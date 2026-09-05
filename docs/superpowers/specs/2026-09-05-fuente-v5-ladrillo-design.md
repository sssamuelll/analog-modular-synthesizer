# Fuente v5 — el ladrillo afuera, la conversión adentro

**Fecha**: 2026-09-05 · **Estado**: **propuesta, sin firmar** (D-V1 a D-V5 en §9) ·
**Decidido por Samuel el 2026-09-05**: sacar la etapa AC-DC de la caja (opción B de
tres), y firmar **D-B2 a 500 mA/riel** para la fila de abajo ·
**Guion**: `hardware/01-power-supply/v5/ladrillo_budget.py` — todas las cifras de
este papel salen de ahí, corriendo ·
**Reabre**: `fuente-v4-liston` §1 (D-F1), §3, §4.1, §4.2, §5 (D-F5), §6, §7 (D-F2);
la spec del chasis §3.2 y §3.3; `calor_budget.py`; `case/cad/params.scad` ·
**No toca**: la cascada de regulación (§4.2 de la v4), que es de donde sale el
0,8 µVrms

---

## 0. Por qué

La v4 mete dentro de una caja de madera: seis módulos AC-DC, la entrada de red,
el fusible, la NTC de arranque, el choke de modo común, los MOV, los Y2 al
chasis, y un recinto de acero de **338,6 × 176,6 × 83 mm** que ocupa el **30 %
del suelo interior**. Con eso, `clearance_budget.py` le encarga al case
**23 666 mm²** de venteo nuevo (#289), que Elke midió como imposibles de sacar
del suelo entero: con la regla de puente del propio repo caben 21 088.

Samuel preguntó por qué un Moog puede ir sellado. La respuesta, con las cifras
de fábrica:

| | potencia | fuente | refrigeración |
|---|---|---|---|
| Moog Subsequent 37 | 13 W | dentro, IEC | ninguna, sellado |
| **SAM17 v4, declarado** | **147,31 W** | dentro | 25 024 mm² de venteo |
| Moog One, 16 voces | 160 W | **fuera**, ladrillo | **ventilador interno** |

Moog sella a 13 W. Al llegar a 160 sacó la fuente **y aun así puso ventilador**.
A la potencia de la v4 la respuesta de Moog no sería «sellado».

Pero los 147,31 W de la v4 son en un 65 % la fila de abajo **a corriente de
placa**: lo que los módulos pueden entregar, no lo que nadie pide. Con la fila
declarada de verdad, el SAM17 no está en la escala del Moog One.

> Fuentes: manual del Subsequent 37 (inMusic, `Subsequent_37_Manual_0.pdf`,
> «13W») y la reseña del Moog One en Sound On Sound (ladrillo de 160 W,
> ventilador interno), leídas el 2026-09-05.

## 1. D-B2, firmada: la fila de abajo declara 500 mA/riel

El 2026-09-04 Samuel corrigió la premisa: *«los otros módulos los vamos a
fabricar nosotros también»*. La fila de abajo no es un censo de invitados de
mercado, es un presupuesto de diseño propio.

El listón «a la altura de la A-100PSU3 o superior» se firmó pensando en módulos
de terceros. **Ese ya no es el supuesto**, y con él cae la razón de declarar
3,8 / 2,5 / 4,0 A.

| | +12 rack | −12 rack | +5 rack |
|---|---|---|---|
| D-F1 (v4, 03-09) | 3,8 A | 2,5 A | 4,0 A |
| **D-B2 (v5, firmada 05-09)** | **0,5 A** | **0,5 A** | **0,5 A** |

Esto no es un recorte de capacidad: es dejar de prometer corriente a módulos que
no existen. La capacidad real la fija la pieza que se elija, y sobra.

## 2. El reparto: qué se va con la fuente y qué no

Lo primero que hay que decir, porque contradice la intuición y decide el resto
del papel:

> **Todo lo que baja por el cordón acaba en calor dentro de la caja.**
>
> El calor lo hacen las CARGAS, y las cargas no se mudan. Lo único que se muda
> es la pérdida de CONVERSIÓN. Así que el calor del cajón es, exactamente, la
> potencia de **salida** del ladrillo.

`ladrillo_budget.py` lo asevera, no lo promete: si algún día entra potencia por
otro sitio, el aserto salta.

De los 147,31 W de la v4, lo que se va con la fuente son **25,02 W** de pérdidas
de conversión y franja de red. Lo demás baja de golpe por otra razón: D-B2.

## 3. El ladrillo (D-V1, D-V2)

**D-V1: la etapa AC-DC es una pieza de catálogo, certificada, fuera de la caja.**
No un cajón nuestro. Un cajón externo multi-riel sería un segundo producto —
chasis, panel, acabado, entrada de red, certificación — y su única ventaja sobre
esta opción es térmica, de **0 W**.

**D-V2: 24 V.** Los 19 V de portátil también bucan bien a los 15,5 de la
cascada, pero a 24 el cordón lleva menos corriente y queda más margen para el
arranque.

| | |
|---|---|
| tensión | 24,0 V |
| salida, lo que baja por el cordón | **64,22 W** |
| corriente del cordón | 2,68 A |
| lo que le pide a la red | 72,98 W |
| **se disipa fuera de la caja** | **8,76 W** |

El cordón es de **dos hilos**, no de siete. Su caída no cae encima de ningún
margen: la absorbe el convertidor de dentro.

| calibre | 1 m | 2 m |
|---|---|---|
| 18 AWG | 112 mV | 225 mV |
| 16 AWG | 71 mV | 141 mV |

Con 16 AWG y 2 m son el **0,6 %** de 24 V. Esta es la diferencia de fondo con
bajar los rieles ya hechos, donde esa misma caída caería justo sobre el margen
de `U1`/`U2` — que es el problema que este papel viene a cerrar, no a empeorar.

## 4. Los rieles de dentro

| riel | V | A | entrega | pierde |
|---|---|---|---|---|
| +12 rack (bus fila B + pantalla) | 12,00 | 1,050 | 12,60 W | 1,40 W |
| −12 rack (bus fila B) | 12,00 | 0,500 | 6,00 W | 1,06 W |
| +5 rack (bus fila B) | 5,00 | 0,500 | 2,50 W | 0,28 W |
| +5 digital (4 × N657 + host USB) | 5,00 | 2,895 | 14,47 W | 1,61 W |
| crudo +cascada (a `U1`) | 15,89 | 0,650 | 10,33 W | 1,82 W |
| crudo −cascada (a `U2`) | 15,89 | 0,650 | 10,33 W | 1,82 W |
| | | | **56,23 W** | **7,99 W** |

El +12 lleva dos cargas por cables distintos: el bus de la fila y la pantalla de
7" con su retorno dedicado, que es lo que pide `pantalla-motor`. Van juntas en
el convertidor y separadas en el cableado.

**Los tres rendimientos son ESTIMADO** y mueven los 7,99 W enteros. Es el único
término de este presupuesto que no está anclado a una hoja, y se cierra
eligiendo las piezas.

## 5. El regalo: la tensión cruda cierra `U2` (D-V3)

`U2`, el pre-regulador negativo, lleva desde el 2026-09-03 con **−170 mV** de
margen de entrada, y no tiene salida por piezas: ninguno de los candidatos de
D-F8 es una pieza negativa. El problema nunca fue `U2`. Es que un IRM de
catálogo entrega 15,0 V con ±2,5 %, y eso no alcanza.

Con un DC-DC nuestro, **la tensión cruda deja de ser un dato de catálogo y pasa
a ser una decisión**:

| crudo | le llega a U1/U2 | margen `U1` | margen `U2` | quema `U2` | |
|---|---|---|---|---|---|
| 15,0 V | 14,370 V | +330 mV | **−170 mV** | 1,61 W | la v4, y su rojo |
| **15,5 V** | 14,851 V | +811 mV | **+311 mV** | 1,94 W | **D-V3** |
| 16,0 V | 15,332 V | +1292 mV | +792 mV | 2,27 W | |

**D-V3: el crudo de la cascada son 15,5 V.** Cuesta **+0,33 W** en `U2`. Un
tercio de vatio por cerrar el único rojo que le queda a la fuente, y **con la
misma pieza**: el LM2991 que el #322 daba por insuficiente.

Tres honestidades sobre esta tabla:

- El margen se aprieta en el corner **bajo** y el calor en el **alto**. No son
  el mismo, y el guion los calcula por separado a propósito.
- **La trampa no es esa, es comparar.** Al escribir la primera versión de este
  papel puse «1,94 W contra los 0,96 de hoy», que son **+0,98 W**: el corner
  alto del nuevo contra el bajo del viejo. En el mismo corner son **+0,33**.
  Por eso la columna de la derecha existe y se calcula con la misma función.
- La tolerancia de ±2,5 % es la de un IRM. Un DC-DC nuestro debería hacerlo
  mejor, y entonces sobra margen. Se declara el conservador.

## 6. Lo que le pasa a la caja

> **ESTA SECCIÓN SE RECALCULÓ ENTERA EL 2026-09-05, DESPUÉS DE PUBLICARLA, Y
> UNA DE SUS CONCLUSIONES ERA FALSA.** Dos defectos, los dos míos:
>
> 1. **Etiqueta y cifra medidas distinto.** El guion que produjo la tabla
>    sumaba la carga ultra y la pantalla *por encima* de `calor_budget.py`, y
>    luego etiquetaba cada fila con la cifra *sin* ellas. Las áreas eran ~5 %
>    mayores que lo que su propia etiqueta decía.
> 2. **La rejilla trasera agrandada sube el centroide de entrada, y eso acorta
>    la chimenea.** La tabla de «trasera a 20 000» lo ignoraba: dejaba la
>    entrada a la altura de hoy. Con el centroide bien puesto, la conclusión
>    que publiqué —«a 30 mm pasa incluso con el `C_D` pesimista»— **no se
>    sostiene**: da 21,4 K contra un techo de 20.
>
> Todo lo de abajo sale ahora de `clearance_budget._tiro()` con las geometrías
> sustituidas y **nada sumado a mano**, que es la única forma de que no vuelva
> a pasar: la cifra sale bien del modelo y se estropea al copiarla fuera.

Área efectiva de hoy: **3 299 mm²**. Techo, 20 K sobre una sala de 45 °C.

| escenario | calor del cajón | hay que abrir (chimenea sola) | con la pared contada |
|---|---|---|---|
| v4 declarada | 147,31 W | 21 725 mm² | 16 555 mm² |
| v4 declarada **+ pantalla** | 150,36 W | 22 244 mm² | 17 074 mm² |
| **v5 declarada** | **64,22 W** | **7 610 mm²** | 2 440 mm² |
| v5 a censo | 35,06 W | 2 657 mm² | 0 |

La comparación honesta es la segunda fila contra la tercera: la v5 lleva la
pantalla dentro de `rieles()` y la v4 no le tiene celda (HUECO 2). Así el
encargo del #289 baja de **22 244 a 7 610 mm²**, un **66 % menos**. Eso cambia
la naturaleza de la obra, no solo su tamaño.

### 6.1 Con el suelo macizo, solo ensanchando la rendija

| rendija | v5 declarada | v5 a censo | v5 declarada, `C_D` pesimista |
|---|---|---|---|
| 4 mm (hoy) | 45,6 K | 30,5 K | 51,0 K |
| 20 mm | 27,8 K | 18,6 K | 31,1 K |
| 25 mm | 26,5 K | 17,7 K | 29,6 K |
| 30 mm | 25,6 K | 17,1 K | 28,6 K |

Con la entrada donde está hoy, **la rendija sola no llega**: ni a 30 mm baja de
25 K con la carga declarada. Hay que agrandar la entrada.

### 6.2 Agrandando la rejilla trasera — y tiene un óptimo

Las ranuras de hoy miden 41,8 mm de alto y su centroide está a y = 46,4.
Agrandar el área las hace **más altas**, y eso sube el centroide y **acorta la
chimenea**. Los dos efectos se pelean, así que hay un máximo:

| trasera | rendija 30 mm: tiro | v5 declarada | v5 a censo | pesimista |
|---|---|---|---|---|
| 7 065 (hoy) | 167 mm | 25,6 K | 17,1 K | 28,6 K |
| 10 000 | 159 mm | 22,1 K | 14,8 K | 24,8 K |
| **20 000** | **129 mm** | **19,1 K** | 12,8 K | 21,4 K |
| 30 000 | 99 mm | 19,7 K | 13,1 K | 22,0 K |

**Pasar de 20 000 empeora.** A 30 000 la entrada tiene 50 % más de área y sale
peor que a 20 000, porque el centroide sube a y ≈ 99 y se come 30 mm de tiro.
Es lo contrario de lo que dice la intuición, y es la razón de que la palanca
buena sea el **suelo** —entra a y = 0 y no le quita altura a nada— y no la
trasera.

### 6.3 Con el suelo abierto (lo que pedía el #327)

Ranuras en la tabla, en serie con el hueco perimetral de las patas de 20:

| suelo | rendija | v5 declarada | v5 a censo | pesimista |
|---|---|---|---|---|
| 20 000 + patas 20 | 20 mm | 19,4 K | 12,9 K | 21,6 K |
| 40 000 + patas 20 | 20 mm | **18,8 K** | 12,6 K | 21,0 K |

### 6.4 La lectura, sin adornos

**Con la carga declarada, ninguna de las geometrías examinadas pasa el techo de
20 K con el `C_D` pesimista.** La mejor —suelo abierto de 40 000, patas de 20,
rendija de 20— da 18,8 K con el `C_D` de la puerta y 21,0 con el exigente.

**Con los censos, todas pasan con holgura**: entre 12,6 y 18,6 K.

Y eso es exactamente HUECO 5. La «v5 declarada» apila **tres peores casos a la
vez**: la fila al techo duro de D-B2 (500 y no 300 mA/riel), la cascada a los
650 mA/riel de D-F1 contra un censo de 334, y el digital al Max de 125 °C del
#256 contra un típico de 0,965 A. Ninguno de los tres es un dato de la caja: son
declaraciones, y dos de ellas están el doble por encima de lo que el instrumento
pide. **Encargar el venteo contra las tres a la vez es una decisión, no una
consecuencia**, y es la que hay que tomar antes de dibujar nada.

> **Los 20 000 mm² de trasera caben, pero solo lo he comprobado en el plano.**
> El campo útil de la trasera va de y = 19,0 a y = 230,2, y la rejilla de hoy
> ocupa 41,8 mm: 46 ranuras de 41,8 × 3,75, 7 065 mm². Llegar a 20 000 pide
> ranuras de ~118 mm, que terminarían en y ≈ 144 y por tanto **por debajo del
> y = 157** donde `guarda_trasera_flexion()` ya declara su HUECO.
> Geométricamente entra. **Lo que NO he verificado es qué le hace a la rigidez
> del PMMA quitarle esa área**, y esa comprobación es del papel del case, no de
> éste. Hasta que se haga, la cifra de 20 000 es una hipótesis de trabajo y no
> un encargo.

Lo que la v5 **no** arregla: la rendija de 25-30 mm sigue arrastrando la franja
del anillo trasero de 23 a ~44 mm, que es el precio estético que Elke identificó
y que choca con «el marco es perfil, no banda». Eso sigue siendo una decisión
del papel del case, no de éste.

Y se va, además de calor:

- **la red entera** de la caja de madera: IEC, fusible, NTC, choke, MOV, Y2 al
  chasis, distancias de aislamiento. Es una clase entera de restricción.
- **el grueso del recinto de acero**, que hoy ocupa el 30 % del suelo. Queda la
  cascada, que es una placa, no un cajón.

## 7. Lo que esto reabre de la v4

| Qué | Por qué |
|---|---|
| **D-F1** | el listón se rehace: D-B2 sustituye 3,8/2,5/4,0 por 0,5/0,5/0,5 |
| **D-F2** (telemetría de rack) | los INA226 medían en los bornes de PS3/PS4; ahora miden a la salida de convertidores nuestros |
| **D-F4** (secuenciador) | usaba los pines ON/OFF de los Mean Well, que ya no están dentro |
| **D-F5** (Y2 al chasis) | **muere**: la red sale de la caja |
| **D-F7** (`PS5` → IRM-45-5) | muere por desaparición del sujeto |
| **§4.1** (fuga a PE) | se rehace: seis fugas menos dentro |
| `calor_budget.py` | su modelo entero es de módulos AC-DC en un recinto |
| `params.scad::potencia_disipada` | 147,31 → 64,22 |

**No se reabre la cascada.** `U1`/`U2`, los LT3045/LT3094 y `U3` se quedan donde
están, con su misma topología, alimentados por un crudo mejor.

### 7.1 Dos issues se quedan sin sujeto

Cruzado contra los issues abiertos, no contra la memoria:

- **#322** — «*hace falta un LDO negativo 300 mV mejor que el LM2991*». Pedía una
  pieza porque `U2` no llegaba con 15,0 V de crudo. **Con D-V3 llega con el
  LM2991 de hoy**: +311 mV. La búsqueda de pieza sobra. Muere por desaparición
  del sujeto, no por haberse resuelto.
- **#130** — «*la entrada de red del chasis no tiene pieza*». No hay entrada de
  red en el chasis. Muere entero.

Y **el PR #316** («el recinto partido, R cerrada y C a la vista») queda **medio
adoptado**: su mitad R se va del edificio, y su mitad C —la cascada fuera de un
cajón de acero— pasa a ser la respuesta a dónde vive lo que se queda. Conviene
leerlo antes de escribir el plan de esta v5, no después.

Ninguno de los tres se toca aquí: este papel no está firmado.

## 8. HUECOS

1. **Los tres rendimientos de los convertidores son ESTIMADO.** Mueven 7,99 de
   los 64,22 W declarados. Se cierran eligiendo las piezas.
2. **La pantalla de 7" sigue sin pieza.** `pantalla-motor` l.250-256 manda su
   fila «cuando la pieza tenga nombre». Entra con 550 mA de +12 V, que son
   6,6 W: no es un redondeo. Es una cita, no una hoja.
3. **#256 sigue abierto.** El digital entra por su máximo a TJ = 125 °C porque
   el punto de trabajo real (85 °C) no está publicado. Entre ese máximo y el
   típico hay **3,0 veces** de corriente.
4. **El coeficiente de la pared exterior sigue sin medir.** Con él, el venteo
   nuevo baja de 8 066 a 2 680 mm². Sin él, no se puede contar. `U_PARED_W_M2K`
   está fuera del veredicto a propósito y este papel no lo cambia.
5. **La cascada declara el doble de su censo.** D-F1 dice 650 mA/riel; el censo
   son 334. Son **20,65 W declarados contra 10,60 reales**, y con D-B2 firmada
   la cascada pasa a ser la línea más gorda del presupuesto. Merece la misma
   pregunta que se le hizo a la fila de abajo. **No se toca en este papel.**

## 9. Lo que hay que firmar

| | Qué | Dónde |
|---|---|---|
| **D-V1** | la etapa AC-DC es **pieza de catálogo certificada**, fuera de la caja; no un cajón nuestro | §3 |
| **D-V2** | el ladrillo son **24 V** | §3 |
| **D-V3** | el crudo de la cascada son **15,5 V**, y con eso `U2` cierra en +311 mV | §5 |
| **D-V4** | los rieles se derivan **dentro** con DC-DC; la cascada no se toca | §4 |
| **D-V5** | el cordón es de **dos hilos**; no bajan rieles hechos | §3 |

Y una que este papel **no** propone y hay que decidir aparte: si la cascada
sigue declarando 650 mA/riel contra un censo de 334 (HUECO 5).
