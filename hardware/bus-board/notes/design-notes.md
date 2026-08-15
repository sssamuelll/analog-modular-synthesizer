# Bus board — notas de diseño

Placa de distribución de ±12 V a los módulos. Se construyen **dos segmentos
idénticos** de 320 × 60 mm; cada uno lleva 6 slots y se alimenta por su propio
par de cables desde el punto de estrella del módulo 1.

Todo lo cuantitativo de aquí sale de [`../ground_budget.py`](../ground_budget.py),
que es ejecutable. Si alguien cambia un ancho de cobre o una longitud de cable,
ese script grita.

---

## 1. El problema no es la corriente, es la afinación

Un bus de alimentación parece un problema de corriente: que llegue tensión
suficiente a todos los módulos. En un sintetizador de 1 V/octava no es eso.

**1 V = 1200 cents, luego 1 mV = 1.2 cents.**

Un CV de tono sale del MIDI/CV referido a *su* masa local y lo lee el VCO
referido a la *suya*. Si las dos masas no están al mismo potencial, la
diferencia se suma al CV. No es ruido — es un error de continua que se oye
como que el instrumento no afina, y que cambia según qué otros módulos estén
consumiendo.

Objetivo del diseño: **≤ 2 cents entre cualquier par de módulos de la cadena de
tono** (MIDI/CV + los tres VCO). Eso son 1.67 mV de diferencia de masa. Es un
número exigente y por eso hay un presupuesto en vez de una intuición.

## 2. La corriente de masa no es la corriente del módulo

La trampa más fácil de este cálculo es usar el consumo del riel como corriente
de masa. No lo es.

Un módulo analógico simétrico chupa *I* de +12 V y la devuelve por −12 V. Por
el pin de masa solo circula el **desequilibrio**. Un VCO con AS3340 consume
~20 mA por riel y desequilibra unos 5 mA.

Lo que sí va íntegro por masa: los LED de panel, y cualquier carga colgada de
un solo riel. Por eso el presupuesto usa **50 mA por módulo SAM17** (el VCO más
una fila de LED, holgado a propósito) y **150 mA por slot Eurorack**, que es
donde puede aparecer un módulo digital con su regulador de 5 V colgado de +12 V
devolviéndolo todo por masa.

## 3. El resultado que no esperaba: el plano es lo fácil

| Contribución | Valor | cents |
|---|---|---|
| Plano de masa del bus, peor par de la cadena de tono | 0.17 mV | **0.20** |
| Cable de bajada SAM17 (150 mm, 2×24 AWG + contactos), 16.8 mΩ | 0.84 mV | **1.01** |
| **Total** | | **1.21** |

El plano aporta **una sexta parte** del presupuesto. Casi todo se lo come el
cable de bajada. Yo entré a este frente convencido de que el trabajo estaba en
el cobre de la placa y está en el mazo de cables.

**Pero solo porque es plano.** La misma masa hecha con una pista de 5 mm son
**+7.1 cents ella sola** y el diseño se cae. El plano no es cinturón y
tirantes: es la única razón por la que el término de la placa es despreciable.

Y de dónde venimos, para que se vea la escala: el daisy-chain con jumpers de la
tesis da entre **6.3 y 30 cents** según lo bueno que sea el crimpado. Los
Dupont crimpados a mano rondan 50–100 mΩ por contacto y ahí está el 30. Se dan
las dos cotas porque la diferencia es 5× y quedarse con la buena sería hacer
trampa.

## 4. En el cable manda el contacto, no el cobre

De los 16.8 mΩ del cable SAM17, **10 son de los cuatro contactos crimpados** y
solo 6.8 del cobre. Consecuencias prácticas:

- Engordar de 24 a 20 AWG apenas mueve la aguja. No lo hagas por esto.
- **Poblar los dos pines de masa de `J2` sí la mueve**: dobla la conductancia de
  golpe. Con uno solo se añade +1.01 cents y el presupuesto revienta.
- Pasar de 150 a 500 mm de cable cuesta +0.95 cents. Los cables cortos no son
  estética.

Y aquí está la razón real de que el peine Eurorack de 16 pines tenga *tres
pares* de masa: **no es redundancia, es conductancia en paralelo**. Seis
conductores de 28 AWG salen a 9.1 mΩ, mejor que dos de 24 AWG (16.8). Doepfer
no puso seis pines de masa por si acaso.

## 5. La regla de reparto que hay que respetar al montar

Con **dos** segmentos aparece un término que no existiría con uno solo: si los
dos tiran corrientes distintas, sus cables de alimentación caen distinto y
*todo* el segmento A se desplaza respecto al B. Con 2.5 mm² y el peor
desequilibrio salen ~1 cent, que sumado a lo demás se pasa de 2.

Se resuelve gratis, sin cambiar un componente:

> **Los cuatro módulos de la cadena de tono (MIDI/CV + VCO1..3) van en el MISMO
> segmento.** Entre ellos el término se cancela porque es común.

Y el corolario: los dos segmentos se alimentan **cada uno desde el punto de
estrella**, con pares de longitud parecida. Encadenar el segundo del primero es
más cómodo de cablear y mete la caída del primero dentro del segundo.

## 6. Plano y masa en estrella no se contradicen

El módulo 1 **rechazó** el vertido de cobre (§7, masa en estrella) y aquí la
masa es un plano sólido. No es una incoherencia:

- En el módulo 1, GND es un **árbol** con muchas ramas que nacen del punto de
  estrella. Un vertido las cortocircuitaría entre sí y destruiría la topología.
- Aquí el bus es **una** de esas ramas, y cada módulo cuelga de ella por un
  único conector. No hay dos caminos que cerrar, luego no hay bucle que crear.

El plano vive *dentro* de una rama. Verificado en el módulo 1 con union-find (0
bucles) y aquí por construcción.

Queda un bucle que no se puede evitar y ya estaba asumido en §13 del módulo 1:
los ~40 jacks de 3.5 mm unen chasis y masa por el casquillo. La consecuencia
buena es que el chasis va en paralelo con el plano y baja la impedancia total;
la mala es que por ahí circula corriente de chasis. Por eso el presupuesto de
arriba **no cuenta con el chasis**: es una cota que se cumple aunque el chasis
no aporte nada.

Y por eso los siete separadores son **de nylon**. Siete espárragos metálicos
unirían el plano al chasis en siete puntos más y meterían esa corriente por el
plano justo donde se mide la afinación.

## 7. El PTC va en los rieles. Nunca en masa

Un PTC de 0.25 A tiene ~1.3 Ω. En un riel de ±12 V eso son 65 mV de caída a
50 mA: irrelevante, el módulo ni se entera y su referencia de tono no depende
del riel.

**En masa serían 94 cents.** Mataría el instrumento por sí solo, y sería un
fallo silencioso: todo funciona, simplemente no afina. Está como aserción en
`ground_budget.py` para que no se cuele nunca.

Elección de valor: Bel Fuse `0ZRE0025FF1E` (0.25 A hold, 0.56 A trip, 240 V,
1.3 Ω típ.). Un módulo en corto arrastra al regulador a su límite (~1.4 A), muy
por encima del disparo. Y el disparo gana la carrera al apagado térmico del
LM2940: el fusible tarda 1–3 s y el disipador tarda decenas de segundos en
llevar la unión a 150 °C.

Un valor más pequeño protegería mejor pero no vale: el `MF-R010` de 0.1 A tiene
hasta 12 Ω y un módulo Eurorack de 150 mA vería casi 2 V de caída. Un solo
valor para los doce, sin dos referencias que confundir al montar.

## 8. El indicador de falla, y su polaridad

Un LED con 4k7 **en paralelo con cada PTC**. Con el PTC intacto caen ~0.1 V y
el LED ni conduce; disparado quedan los 12 V y se enciende a ~2 mA. Señala qué
conector y qué riel falló sin un solo componente activo.

No le roba el disparo al PTC: un `0ZRE0025FF` a 12 V pide ~40 mA para
mantenerse caliente, y 2 mA sobre eso es un 5 %.

La polaridad es la trampa fina. En +12 V la corriente cae del riel al módulo; en
−12 V sube del módulo al riel. Dibujando los dos bloques con **el lado que está
a más potencial arriba**, los dos LED quedan con el ánodo arriba y son
idénticos. Dibujado "de abajo arriba" el de −12 V sale invertido y no
encendería jamás — y es un fallo que solo se descubre el día que hay una avería.

Lo que el indicador **no** cubre, dicho claro: si el PTC dispara y después el
módulo se queda en circuito abierto, no hay corriente y el LED no enciende. Es
un caso que en la práctica no ocurre (lo que dispara el fusible es una carga que
sigue ahí), pero el indicador dice "fusible abierto **y** el módulo sigue
cargando el riel", no "fusible abierto".

## 9. Los dos conectores, y por qué uno lleva llave y el otro no

| | SAM17 (`P1..P6`) | Eurorack (`J1..J6`) |
|---|---|---|
| Conector | Molex KK-254 4 pines | Tira 2×8 de 2.54 mm |
| Llave | **Sí** | **No — prohibida** |
| Orden | +12 / GND / GND / −12 | ver abajo |

Doepfer lo dice sin margen: *"it's not allowed to use bus boards with polarized
pin headers (boxed pin headers with code gap). These force the user to connect
the bus cable in a certain direction which may be the wrong one"*. La
orientación la marca la franja roja del cable, que va al par **−12 V**, y ese
par va serigrafiado.

En el peine SAM17 la llave sí se quiere: es un conector propietario, no hay
estándar ajeno que respetar, y la llave impide invertirlo.

Pinout Eurorack, por pares, desde la franja roja:

| Par | Pines | Señal | En esta placa |
|---|---|---|---|
| 1 | 1, 2 | **−12 V** (franja roja) | conectado |
| 2–4 | 3–8 | GND | conectado (6 pines) |
| 5 | 9, 10 | **+12 V** | conectado |
| 6 | 11, 12 | +5 V | **NC** |
| 7 | 13, 14 | CV | **NC** |
| 8 | 15, 16 | Gate | **NC** |

Los dos pines de cada par van al mismo sitio, como manda Doepfer (*"left and
right pins are always connected on the bus board"*).

**El +5 V se deja sin conectar a propósito.** El +5 V del SAM17 sale por `J6`
del módulo 1 con retorno dedicado, porque el backlight del LCD va conmutado
(§10.1). Meterlo en este bus le devolvería la corriente por la masa de audio, que
es exactamente lo que ese retorno dedicado evita. Doepfer también lo da por
opcional. Consecuencia asumida: **un módulo Eurorack que necesite +5 V del bus no
funcionará aquí**, y va serigrafiado como NC para que se vea antes de comprarlo.

## 10. Ruteo: nada que no sea masa baja a la capa inferior

Consecuencia directa de §3. Una vía de +12 V atravesando el plano le abre una
ranura; la corriente de retorno tiene que rodearla y el plano deja de ser plano
justo donde se mide. Por eso:

- **B.Cu**: solo la zona de GND. Cero pistas, **cero vías**.
- **F.Cu**: los tres rieles (dos franjas vertidas, arriba +12 V y abajo −12 V) y
  los nodos locales de cada slot.

Esto obliga a montar el peine Eurorack **girado 180°**, con el par de la franja
roja abajo. Del otro lado, cada slot tendría que cruzar `+12S` por encima de
`−12S`, y sin poder bajar a la capa inferior no hay por dónde. `build_pcb.py` lo
comprueba pad a pad antes de rutear.

## 11. Verificaciones

Todo esto se corre y tiene que salir en verde:

```
python ground_budget.py          # presupuesto de masa, con autocomprobación
python kicad/build_schematic.py  # ERC vía kicad-cli
python kicad/check_netlist.py    # netlist contra el diseño declarado a mano
python kicad/check_bom.py        # cruce esquemático <-> bom.csv
"<kicad>/bin/python.exe" kicad/build_pcb.py   # DRC vía kicad-cli
```

Estado actual:

| Comprobación | Resultado |
|---|---|
| Presupuesto de masa | **1.21 cents** (objetivo ≤ 2) |
| ERC | **0 infracciones** |
| Netlist contra diseño | 27 redes, 160 pines, **cuadran una a una** |
| DRC | **0 infracciones, 0 elementos sin conectar** |
| Vías | **0** |
| Masa en B.Cu | verificado por id de capa |
| Cruce BOM | 49 en la hoja, 49 cruzados |

El ERC saliendo a cero **no** basta y por eso está `check_netlist.py`: una hoja
con +12 V y −12 V intercambiados pasa el ERC con cero avisos y fríe todos los
módulos que se enchufen.

## 12. Lo que NO está confirmado

1. **El orden de filas del peine Eurorack.** De fuente primaria de Doepfer está
   confirmado el juego de señales, que la franja roja es −12 V y va abajo, y que
   CV y Gate ocupan los dos pares de arriba. El orden exacto del bloque central
   (GND×3 y luego +12 V) viene de fuentes secundarias coincidentes, no de una
   tabla oficial: todas las páginas remiten a una imagen. **Equivocar esa fila
   destruye cualquier módulo que se enchufe.** Antes de fabricar hay que
   verificarlo con un polímetro contra un cable Doepfer o un módulo real —
   mismo trato que `BR1` en el issue #11.
2. **La resistencia de contacto de 10 mΩ** por crimpado es valor de manual, no
   medido. Es el término que más pesa del presupuesto. Se mide con un
   miliohmímetro o por caída a 1 A.
3. **La corriente de mantenimiento del PTC disparado** (~40 mA a 12 V) sale de
   la física del equilibrio térmico y del dato de disipación del datasheet, no
   de la curva concreta a 12 V. Si fuese mucho menor, la rama del LED podría
   desengancharlo y hacerlo oscilar.
4. **El tiempo de disparo a 1.4 A** se ha estimado en 1–3 s de las curvas
   típicas de la familia. La carrera contra el apagado térmico del LM2940 se
   gana con holgura, pero conviene leer la curva de la pieza comprada.
5. **El desequilibrio de 5 mA del AS3340** es una estimación. Si un módulo
   resultara mucho más asimétrico, sube su término del presupuesto en
   proporción directa.
6. `ZONE_FILLER.Fill()` de `pcbnew` **revienta el proceso** (access violation)
   sobre una placa construida en memoria; hay que guardar, recargar y rellenar.
   Es una limitación de la herramienta, no del diseño, pero está documentada en
   `build_pcb.py` porque cuesta una tarde encontrarla.
