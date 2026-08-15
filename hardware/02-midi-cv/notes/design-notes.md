# Módulo 2 — MIDI/CV: notas de diseño

El único módulo mixto del sintetizador: un Raspberry Pi manda un DAC de 16 bits
por SPI, y de ahí salen tres CV de 1 V/octava y un GATE de 10 V.

Los números vienen de [`../tuning_budget.py`](../tuning_budget.py), que es
ejecutable y se compone con el presupuesto de masa del bus board.

---

## 1. Lo que la calibración absorbe y lo que no

Esta distinción organiza el módulo entero, y sin ella el presupuesto no
significa nada.

El firmware guarda una tabla de afinación por nota (`tuning.json`, 84 notas).
Esa tabla **absorbe cualquier error estático y repetible**: el offset del
amplificador, el error de ganancia de las resistencias, la no linealidad del
DAC. Se calibra una vez con un afinador y desaparece.

Lo que **no** puede absorber es lo que cambia *después* de calibrar: la deriva
térmica, el ruido, y el error de masa — que depende de lo que estén consumiendo
los otros módulos en ese instante.

Los números, con TL074H y ±20 °C de excursión desde la calibración:

| | cents |
|---|---|
| **Estáticos** (se calibran, no cuentan) | **103.0** |
| deriva de la referencia (2 ppm/°C) | 0.34 |
| deriva de offset del amplificador (2 µV/°C) | 0.13 |
| masa del bus board | **1.21** |
| **Presupuesto real** | **1.68** |

Dos cosas que salen de ahí y que no eran obvias:

1. **Los errores estáticos suman 103 cents y no importan ninguno.** Casi todo es
   la tolerancia del 1 % de la red de ganancia (84 cents) y el offset del
   amplificador. Cambiar a resistencias del 0.1 % sería tirar dinero.
2. **De los 1.68 cents que sí cuentan, 1.21 son la masa.** La electrónica de
   este módulo aporta 0.47. El bus board era la prioridad correcta, y este
   módulo solo tiene que no ser el cuello de botella — cosa que consigue.

Corolario para elegir piezas: **gana la que menos DERIVA, no la que menos
offset tiene.**

## 2. TL074H, no TL074

Es la consecuencia directa de §1, y es la única pieza donde la letra importa.

| | TL074C clásico | **TL074H** |
|---|---|---|
| Salida garantizada | ±12 V a ±15 V → **3 V de margen al riel** | 115 mV típ / 210 máx |
| Offset | 3 mV típ / 13 mV máx | 1 mV típ / 4 mV máx |
| **Deriva de offset** | **18 µV/°C** | **2 µV/°C** |

El clásico tiene además un problema de recorrido: con 3 V de margen, sobre
rieles de ±12 V solo garantiza ±9 V, y **la tesis pide un CV de hasta 10 V**.
No llega, por 1 V.

Eso se arregla bajando el rango (§3) — y entonces el clásico sí llega, con 2 V
de sobra. Así que **el motivo real de preferir el H no es el recorrido, es la
deriva**: 1.21 contra 0.13 cents, 9× peor, y en la única columna que la
calibración no puede tocar.

## 3. El CV baja de 3–10 V a 0–7 V

Mismo span de 7 octavas (C1–C8), misma resolución en cents, y 3 V más de margen
contra el riel. Un LSB del DAC son **0.128 cents** con cualquiera de los dos
rangos: la resolución depende del span, no de dónde esté centrado.

El offset absoluto no importa porque el conversor exponencial del VCO lo absorbe
con su trimmer de tono grueso, que hay que ajustar de todas formas.

Es una desviación de la tesis, y se documenta como tal: **el módulo 3 tiene que
diseñarse contra 0–7 V**, no contra 3–10.

## 4. Dos masas que no se tocan en esta placa

La decisión estructural del módulo.

- **`GNDA`** llega por `J1` (el bus de ±12 V) y es la referencia de todo lo
  analógico: la patilla GND del DAC, los amplificadores, los casquillos de los
  jacks.
- **`GNDD`** llega por `J2`, que es el retorno **dedicado** que el módulo 1 saca
  junto al +5 V ([§10.1](../../01-power-supply/notes/design-notes.md)) porque el
  backlight del LCD va conmutado.

Se unen en el punto de estrella del módulo 1 y **en ningún otro sitio**.

El número que lo justifica: si se juntaran aquí, la corriente del backlight
tendría dos caminos de vuelta y parte se iría por la masa analógica. 100 mA
sobre unos 50 mΩ son 5 mV, que amplificados por 2.8 son 14 mV — **17 cents de
desafinación que aparecen y desaparecen según el brillo de la pantalla.**

Lo que sí cruza de un dominio al otro son las señales lógicas (SPI, LCD,
botones, gate). Da igual: el desnivel entre las dos masas son milivoltios y los
umbrales lógicos son cientos de milivoltios.

Y por eso **el DAC tiene VDD en +5 V pero GND en `GNDA`**: su miliamperio de
consumo vuelve por la masa analógica, que es donde tiene que estar referida su
salida. Un mA sobre la masa del bus son 17 µV, 0.02 cents.

## 5. `VLOGIC` va a +3V3, no a +5 V

El AD5686R tiene una patilla de alimentación de E/S aparte, admisible entre
1.8 y 5.5 V. Es la que decide los umbrales lógicos.

Atada a VDD = 5 V, el umbral V<sub>IH</sub> sube a 0.7 × 5 = **3.5 V**, y el
Raspberry Pi entrega 3.3 V. Se queda por debajo: el SPI funcionaría a ratos y
fallaría al calentarse, que es el peor modo de fallo posible porque no es
reproducible en el banco.

Con `VLOGIC` a 3.3 V el umbral baja con ella y el margen vuelve a ser el de
diseño. Está comprobado en `kicad/check_netlist.py`, no solo escrito aquí.

## 6. El GATE lleva dos MOSFET, y son dos por una razón

Una sola etapa invierte. Y un gate invertido significa que **al encender, antes
de que arranque el firmware, el GPIO está en alta impedancia y todas las
envolventes dispararían.**

Con dos etapas el reposo es gate **bajo**: Q1 en corte → su drenador arriba →
Q2 en conducción → salida a cero. `R14` además fija la puerta de Q1 a masa para
que no quede flotando durante los segundos que tarda el Pi en arrancar.

El nivel de 10 V lo pone el divisor `R12`/`R13` (12 × 10/12), y la cuarta unidad
del TL074H lo amortigua para que la salida no dependa de la carga.

## 7. Dos trampas del AD5686R que cuestan una placa

**El encapsulado.** El pinout del TSSOP-16 y el del LFCSP-16 van **desfasados
dos pines**. El símbolo de `kicad/sam17.kicad_sym` está dibujado contra el
TSSOP (figura 7 del datasheet) y `build_schematic.py` lo verifica patilla a
patilla antes de generar nada. El LFCSP lleva además pad térmico que hay que
soldar a masa.

**El grado.** El AD5686R-**EP** (*enhanced product*) es **peor** que el
comercial pese al nombre: INL ±4 LSB contra ±2, y referencia de 13 ppm/°C máximo
contra 5. La primera versión del presupuesto usó los números del -EP porque fue
el PDF que salió primero al buscar, y daba un peor caso de 3.53 cents en vez de
2.19. Hay que leer la hoja del grado que se compra.

Dos ataduras que no se ven en el esquemático pero deciden el arranque:

- **`GAIN` a masa** = ganancia ×1 → salida 0–2.5 V. Arriba serían 0–5 V, y con
  VDD = 5 V la salida se comprime justo en el último tramo, que es donde están
  las notas agudas.
- **`RSTSEL` a masa** = arranca a fondo de escala **cero**, o sea CV = 0 V.
  Arriba arrancaría a media escala y el sintetizador soltaría una nota sola al
  encender.

## 8. Verificaciones

```
python tuning_budget.py            # presupuesto de afinación, con aserciones
python kicad/build_schematic.py    # ERC vía kicad-cli
python kicad/check_netlist.py      # conectividad contra el diseño declarado
python kicad/check_bom.py          # cruce esquemático <-> bom.csv
```

| Comprobación | Resultado |
|---|---|
| Presupuesto dinámico | **1.68 cents** (objetivo ≤ 5) |
| Resolución | 1 LSB = **0.128 cents** |
| ERC | **0 infracciones** |
| Netlist | 63 redes; masas separadas, DAC atado, 3 canales completos, gate no inversor |
| Cruce BOM | 42 en la hoja, 42 cruzados |

Un detector nuevo, en [`../../tools/schcheck.py`](../../tools/schcheck.py):
reconstruye la conectividad como la ve KiCad (extremos que coinciden, extremos
que caen sobre otro cable, solapes colineales) y exige que cada grupo tenga
**un solo nombre de red**. Nació porque esta clase de fallo ya se había colado
dos veces hasta el ERC:

- en el bus board, la bajada de masa del peine terminaba encima del ramal de
  `+12S`;
- aquí, los rabitos de dos pull-ups contiguas se solapaban porque el paso entre
  filas era menor que el componente con sus rabitos — y los cuatro botones
  quedaron colgados de `+3V3`.

Está probado contra ese segundo caso: revirtiendo el paso, el detector lo caza.

## 9. Lo que NO está confirmado

1. **Nada de esto está medido.** El presupuesto es de datasheet. Lo primero a
   medir sobre placa real es la **deriva del CV con la temperatura**: encender
   en frío, calibrar, dejar una hora cerrada y volver a medir las 84 notas.
2. **Los 20 °C de excursión** son una estimación de cuánto sube un cajón cerrado
   con tres reguladores dentro. Si fuesen 40, el presupuesto se dobla a 3.4
   cents — sigue pasando, pero conviene medirlo con un termopar.
3. **El consumo real del backlight.** El presupuesto del riel de +5 V se hizo
   contra los 100 mA del peor caso; con `R16` = 47 Ω salen ~17 mA. Si alguien
   pone un LCD con backlight de matriz, vuelve a subir.
4. **El desequilibrio de corriente de este módulo** entra en el presupuesto de
   masa del bus board como 50 mA. Aquí lo analógico consume poco (un TL074H y un
   DAC), así que debería sobrar, pero está sin medir.
5. **El firmware todavía no existe** más allá de un stub. El cambio de rango
   (§3) y el mapa de pines de `J3` hay que reflejarlos en `software/midi-cv/`.
6. **La PCB no está ruteada.** Esta tanda cierra el esquemático; el layout es el
   paso siguiente, y tiene una restricción fuerte que ya se puede anticipar: las
   dos masas tienen que llegar cada una a su conector **sin tocarse en ningún
   punto del cobre**.
