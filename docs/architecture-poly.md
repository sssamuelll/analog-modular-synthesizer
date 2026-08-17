# Arquitectura polifónica del SAM17

> Este documento **sustituye** al diagrama monofónico de
> [`architecture.md`](architecture.md) como diseño vigente. Aquel queda como
> referencia de lo que hace la tesis, que es el punto de partida y no el
> destino.
>
> La parte digital — el micro de tiempo real, la computadora externa y el
> agente de IA — está en
> [`architecture-compute.md`](architecture-compute.md).

El SAM17 pasa a ser un **sintetizador polifónico de 4 voces**. Cada nota tiene
su propio oscilador, su propio filtro, su propio VCA y su propia envolvente.

---

## 1. El principio que lo ordena todo

**Los mandos se comparten; los circuitos se replican.**

Un filtro de 4 voces no son cuatro paneles. Es **un panel con un juego de
perillas y cuatro circuitos idénticos detrás**, todos recibiendo la misma
tensión de control. Cuando giras el corte, gira en las cuatro voces a la vez —
que es lo que quieres, porque las cuatro voces son el mismo instrumento tocando
un acorde, no cuatro instrumentos distintos.

Consecuencia práctica: **el panel no crece con las voces, la PCB sí.** Pasar de
4 a 6 voces no pide más sitio en el cajón, pide más cobre. Por eso la decisión
de cuántas voces se puede posponer sin rehacer el frontal.

Y consecuencia de diseño para los módulos 3, 5, 6 y 7: cada uno es **una placa
de 4 canales con un solo juego de controles**, no cuatro placas.

## 2. El cerebro

El módulo 2 deja de ser "el conversor MIDI a CV" y pasa a ser el que reparte las
voces. Es donde empieza la polifonía.

> **El instrumento entero vive en un microcontrolador** (RP2350 en Rust
> bare-metal): reparto de voces, CV, gates, autoafinado, secuenciador. La
> computadora es **opcional, externa y puede ser cualquiera** — se enchufa por
> USB MIDI y trae tu DAW y tus plugins. El instrumento **toca sin ella**, y sigue
> sonando si se cae. Detalle en
> [`architecture-compute.md`](architecture-compute.md).

Lo que hace:

- **Asignación de voces.** Decide qué nota va a qué voz, con robo de voz cuando
  llegan más notas que voces. Es una decisión de software y por eso vive aquí.
- **El valor de cada CV** — tono a 1 V/octava, velocity, y los mandos de §7.
  Ya no salen de aquí como voltaje: salen como **números por el enlace serie**
  (§8), y el voltaje lo fabrica el DAC del módulo que lo consume.
- **4 gates** independientes.
- **Autoafinado** de los cuatro osciladores, midiendo las cuatro a la vez
  sobre pulsos lógicos que le llegan del módulo 3 (§5).
- **La interfaz**: pantalla pequeña con encoders — modelo y mandos sin
  confirmar ([`architecture-compute.md`](architecture-compute.md) §9).

## 3. Diagrama de bloques

```
        USB MIDI ──┐
        DIN MIDI ──┤
                   ▼
        ┌──────────────────────────────────┐
        │       MÓDULO 2 — EL CEREBRO      │
        │  RP2350 (Rust bare-metal)        │
        │  asignación de voces + autoafinado│
        └───────┬─────────────┬────────────┘
          SERIE │     GATE 1-4│              escucha
           (§8) ▼             ▼ (al ADSR)      ▲
     ┌─────────────────────────────────┐       │
     │  MÓDULO 3 — VCO x4              │       │
     │  DAC + 4x SSI2130 + 74HC14      │───────┘  4x pulso logico
     │  un juego de mandos             │          (TUNE_OUT digital)
     └────┬────┬────┬────┬─────────────┘
          ▼    ▼    ▼    ▼
     ┌─────────────────────────────────┐
     │  MÓDULO 5 — VCF x4              │  ← corte y resonancia
     │  4x LM13700, un juego de mandos │     comunes a las 4
     └────┬────┬────┬────┬─────────────┘
          ▼    ▼    ▼    ▼
     ┌─────────────────────────────────┐     ┌──────────────┐
     │  MÓDULO 7 — VCA x4              │◄────│ MÓDULO 6     │
     │  4x LM13700                     │ env │ ADSR x4      │
     └────┬────┬────┬────┬─────────────┘     └──────────────┘
          ▼    ▼    ▼    ▼                      ▲
     ┌─────────────────────────────────┐        │ GATE 1-4
     │  MÓDULO 4 — MIXER 4:1           │        │
     └────────────┬────────────────────┘
                  ▼
             AUDIO OUT
```

El enlace serie (§8) llega igual a los módulos 5, 6 y 7 — el diagrama solo
dibuja la cadena de audio para no enredarse.

El mixer se mueve **al final**. En el diseño monofónico sumaba los tres VCO
antes del filtro; aquí no puede, porque cada voz tiene que atravesar su propio
filtro y su propio VCA antes de mezclarse con las demás. **Sumar antes sería
parafónico, no polifónico** — y es exactamente la diferencia entre los dos.

## 4. Convenciones eléctricas

| Señal | Rango | Cantidad | Notas |
|-------|-------|----------|-------|
| `CV_PITCH_n` | **0 – 7 V** | 4 | 1 V/oct, 7 octavas (C1–C8). Cambia respecto a los 3–10 V de la tesis: ver issue #18. **No cruza entre módulos**: nace en el DAC de la placa del VCO (§8) |
| `CV_VEL_n` | 0 – 7 V | 4 | Velocity por voz. Nace en el DAC de la placa del VCA (§8) |
| `GATE_n` | 0 / 10 V | 4 | Activo alto |
| `TUNE_OUT_n` | **lógico 3.3 V** | 4 | **Nuevo**: onda del VCO ya recortada, para medir su frecuencia. Digital a propósito (§5). Viaja en el mismo mazo J2 que `SERIE` (fila siguiente), no en un cable aparte |
| `SERIE` | lógico 3.3 V | 12 hilos, IDC 2×6 | **J2**, el conector IDC del mazo digital del módulo (spec del módulo 3): SPI + CS por módulo + I²C de telemetría + `TUNE_OUT`×4 + `GNDD`×2, todos en el mismo mazo (§8). Direccionamiento cerrado: híbrido CS-por-módulo con cadena soldada en placa (issue #34) |
| `+12V` / `-12V` | ±12 V | — | 650 mA por riel |
| `+5V` | 5 V | — | Solo el módulo 2. Los módulos con DAC se hacen su lógica con regulador local desde +12 V (§8). **La pantalla NO cuelga de aquí** (§9) |
| `GNDA` / `GNDD` | — | — | Masas partidas, se unen solo en la estrella del módulo 1 |

## 5. Los dos caminos de señal, que no se tocan

Es la decisión que resuelve el dilema entre "quiero un instrumento modular" y
"quiero que se afine solo". Parecen incompatibles hasta que ves que son **dos
caminos distintos** que casualmente son los dos audio analógico.

### El camino de sonido

VCO → VCF → VCA → mixer → salida, y todo lo que el usuario quiera enrutar.
**Aquí vive la modularidad**, y va por el patch bay (§6).

### El camino de afinación

El cerebro escucha a cada oscilador para medirle la frecuencia. Eso **no es
sonido, es instrumentación** — como el cable de un afinador. Dos propiedades que
lo definen:

- **Va antes del filtro, siempre.** Se afina el oscilador, no el resultado
  filtrado. Con el filtro cerrado no habría nada que medir.
- **Es permanente e invisible.** A un afinador no se le patchea.

**Los dos caminos no comparten un solo cable.** Esa separación es lo que permite
patchear lo que sea sin quedarse nunca sin autoafinado.

### Y el camino de afinación es DIGITAL

A la medida no le hace falta el audio: solo necesita saber cuándo la onda cruza
por cero. Así que **el recorte se hace en el propio módulo del VCO** con un
disparador Schmitt, y lo que viaja hasta el cerebro es un **pulso lógico**.

Lo que eso cambia respecto a mandar la señal analógica:

| | Analógico | **Pulso lógico** |
|---|---|---|
| Diafonía con la alimentación | se la come | **inmune** |
| Ensucia el bus con audio | sí | **no** |
| Piezas en el cerebro | mux + atenuador + acoplo + Schmitt + fuente de −5 V | **un pin** |
| Medir las 4 voces a la vez | no, el mux va de una en una | **sí** |

Cuesta **un chip** en el módulo 3: un 74HC14 lleva seis disparadores, así que
uno cubre los cuatro osciladores y sobran dos.

Y para la modularidad es lo importante: **la interfaz de autoafinado pasa a ser
digital y documentada**. Cualquier oscilador futuro es autoafinable con solo
sacar un pulso lógico. Eso es mucho más modular que «mándame tu salida
analógica».

> Esto **sustituye** al multiplexor 74HC4051 que figuraba en la versión anterior
> de este documento. El mux resolvía el problema equivocado: ahorraba pines a
> costa de meter audio analógico en el cerebro y de medir de una en una.

### Cómo mide

**Conteo recíproco**: se cronometra cuánto tardan N periodos y se saca
`f = N/T`. Es lo contrario de contar ciclos por segundo, y es mucho mejor en las
notas graves — que es donde el otro método se queda corto.

Los números están en
[`hardware/02-midi-cv/autotune_budget.py`](../hardware/02-midi-cv/autotune_budget.py),
que es ejecutable:

| | |
|---|---|
| Barrido completo 84 notas × 4 voces | **3.5 s** — las cuatro en paralelo |
| Lo mismo de una en una, como exigía el mux | 14.1 s |
| Precisión de la medida | **0.5 cents** peor caso |
| Coste en pines del cerebro | **4 GPIO**, uno por oscilador |

### Lo que esto le hace al presupuesto de afinación

[`tuning_budget.py`](../hardware/02-midi-cv/tuning_budget.py) separa los errores
en los que la tabla de afinación absorbe y los que no. **El autoafinado mueve
casi todos al lado de los absorbidos**, porque recalibrar deja de costar una
tarde con un afinador.

Lo único que sigue sin absorberse es el **error de masa**: depende de lo que
estén consumiendo los otros módulos en ese instante, así que cambia después de
calibrar. Y ese error se encogió al mudar el DAC a la placa del VCO (§8) — el
CV de tono ya no cruza el bus, solo el plano local del módulo.

| | cents |
|---|---|
| Masa local del módulo del VCO (§8) | 0.08 |
| Medida del autoafinado | **0.50** |
| **Suelo del instrumento** | **0.58** |

(Era 1.71 cuando el CV de tono cruzaba el bus: 1.21 de masa + 0.50 de medida.
Ese 1.21 sigue vigente — pero para el CV *patcheado*, no para el pitch.)

Y la deriva del VCO — que sin autoafinado no está acotada, porque el convertidor
exponencial arrastra −0.33 %/°C y su compensador hay que ajustarlo — **deja de
contar**.

O sea: el suelo del instrumento pasa a ser **la medida del autoafinado**, que
es exactamente donde quieres tenerlo — porque la medida mejora con software y
paciencia, y la masa solo con cobre.

Una propiedad que sale gratis: el VCO suena siempre y el gate solo abre el VCA,
así que **el autoafinado corre en silencio**.

## 6. El patch bay: normalizado

Modularidad total y polifonía tiran en direcciones opuestas, y conviene verlo
antes de decidir: **en un modular cada cable lleva una señal. Con 4 voces, cada
conexión son 4 cables.** Un patcheo básico de un sinte de 4 voces serían 16
cables solo para que suene. Eso no es libertad, es un estorbo.

Los poly de verdad lo resuelven normalizando la cadena de voz y dejando
patcheable la modulación y las excepciones. Aquí se hace lo mismo, pero sin
renunciar a nada:

- **Nada enchufado** → es un poly de 4 voces que suena solo, cero cables.
- **Un cable enchufado** → **rompe el normalizado de esa conexión** y enrutas a
  tu gusto, incluyendo sacar una voz suelta y meterla por donde quieras.
- **Y la afinación** corre por su carril digital pase lo que pase.

### Dónde vive el normalizado

**En los jacks de cada módulo, no en un módulo aparte.** El jack elegido —el
Thonkiconn `WQP-PJ398SM`, el mismo que ya está en el BOM del módulo 2— tiene tres
patillas: punta, masa y **`TN`**, que es el contacto que se abre al meter un
cable. Ese pin **es el mecanismo del normalizado**.

En el módulo 2 quedó sin conectar y documentado como «un muelle mecánico que en
este módulo no se usa». En un instrumento patcheable **ese pin es la pieza
central**, y hay que conectarlo en todos los módulos.

## 7. Los mandos salen del camino de audio

Decisión estructural, y la que hace posibles los presets.

**Un potenciómetro es su propia memoria**: su posición física *es* el valor.
Cargas un preset y la perilla sigue donde la dejaste. Por eso el Minimoog no
tiene presets — no es que no quisieran.

La salida: **las perillas dejan de controlar y pasan a ser sensores.** Van a un
ADC, el micro las lee, y **el voltaje de control lo genera un DAC**. El audio
sigue siendo 100 % analógico; lo que se digitaliza es el *mando*, no el sonido.

Un preset pasa a ser **una lista de números**. Guardarlo es trivial.

### Esto no es un injerto, es usar los chips como fueron diseñados

Mira cómo se llaman los módulos: **VCO, VCF, VCA** — *Voltage Controlled*.

El CEM3340 tiene entrada de CV dedicada. El LM13700 se controla por corriente de
polarización. En el diseño original **el potenciómetro no está en el audio: está
fabricando un voltaje de control a mano.**

O sea que el pote siempre fue la versión tosca de lo que el DAC hace fino. No
nos metemos en medio de nada: hacemos el mismo trabajo, en el mismo sitio, con
más precisión y sin desgaste.

### Tres casos, tres herramientas

Cada parámetro cae en uno de estos, y usar la herramienta equivocada cuesta
rediseño o calidad:

| Caso | Solución | Ejemplos |
|---|---|---|
| **Tiene entrada de CV** | **DAC**. El audio no lo toca | corte del filtro, PWM, nivel del VCA, afinación |
| **El pote estaba EN el audio** | **VCA controlado por CV** (otro LM13700), nunca un digipot | resonancia en filtro tipo MS-20, niveles de mezcla |
| **El pote es el elemento de tiempo** | **digipot o OTA** como resistencia variable | tiempos del ADSR, que son una RC |

El tercero merece decirse claro: **los tiempos de una envolvente analógica los
fija una RC**, y ahí el pote *es* la resistencia. Eso no se resuelve con un CV:
hace falta una resistencia controlable — un OTA en modo resistor, un JFET, o un
digipot tipo **AD5293** (±16.5 V, 1024 pasos, 1 % de tolerancia y 5 ppm/°C como
divisor, que para un digipot es excepcional).

Y el segundo también: en la resonancia y en la mezcla, meter un digipot pone
**switches MOSFET en el camino de audio** — distorsión y resistencia de cursor.
Un VCA saca el control del camino otra vez, que es todo el punto.

### Lo menos invasivo, ordenado

| | Qué le hace al audio |
|---|---|
| **DAC → entrada de CV** | **Nada.** No está en el camino |
| Pote motorizado | Nada tampoco — *es* el circuito original. Pero conserva sus defectos: 20 % de tolerancia, cientos de ppm/°C, y se raya con los años |
| Digipot | Switches en el camino: distorsión, resistencia de cursor, escalones |

### Cómo se leen las perillas

**Multiplexor analógico + un canal de ADC**, escaneando en bucle. Son ~15-20
perillas y el micro no tiene tantos ADC; un 4051 o un 4067 las recorre a unos
cientos de hercios, que sobra para un mando humano.

(Es el mismo tipo de chip que se descartó para el autoafinado, y ahí sí encaja:
leer perillas no tiene prisa, medir frecuencia sí.)

### El desfase de la perilla: soft takeover con LED

Al cargar un preset la perilla queda donde estaba. Se resuelve sin mecánica:

**La perilla no manda hasta que la pasas por el valor guardado.** Y un **LED por
perilla** te dice si vas por encima o por debajo — verde cuando engancha.

Es soft takeover **hecho visible**, y cuesta un LED contra los €15-30 de un pote
motorizado, sin mecánica, sin corriente de motor y sin fondo de panel. Como los
paneles ya llevan LEDs direccionables encadenados, **la línea de datos ya está
ahí**.

Los potes motorizados quedan como opción futura para dos o tres mandos, si al
usarlo resulta que hace falta. Los **servos de hobby no sirven**: su reductora no
se deja girar a mano, y una perilla que no puedes girar no es una perilla.

### Lo que esto compra, además de los presets

**Hace que el agente sirva de algo.** Con todos los parámetros en digital, la IA
puede **crear sonidos** — no solo hablar de ellos. Sin esto podría decirte «sube
la resonancia» pero no subirla.

Y de paso: automatización desde la DAW, morphing entre presets, modulación de
cualquier parámetro por LFO digital, y recall total con el proyecto (que es lo
que hace valer el VST compañero).

### Los LEDs de panel

**Direccionables (WS2812B / SK6812)**: una sola línea de datos encadena todos los
paneles. Color por preset o por banco, y de un vistazo sabes dónde estás.

Dos avisos:

**Van en `GNDD`, nunca en `GNDA`.** Un WS2812 conmuta corriente a decenas de kHz
y su línea de datos es un tren de pulsos rápidos. Es el mismo argumento que sacó
el backlight del LCD de la masa analógica.

**El acrílico naranja filtra el color.** Iluminando *a través* del cuerpo, los
azules y verdes se mueren y todo tiende a naranja. Si el código de color tiene
que leerse, los LEDs van en la cara del panel — que es PCB de aluminio y sirve —
o hacen falta ventanas de acrílico transparente.

## 8. Los DAC viven en los módulos, no en el cerebro

La consecuencia de §7 llevada a su sitio. Si el DAC fabrica los voltajes de
control, la pregunta es dónde vive — y la respuesta cómoda, «todos en el
cerebro y un cable por CV», tiene un defecto estructural: **el mazo de cables
crece con voces × parámetros.** Son ~15-20 CV hoy, más si crecen las voces, y
cada módulo nuevo pide re-cablear el instrumento.

La decisión: **cada módulo lleva los DAC — y digipots — de sus propios
parámetros, y del cerebro sale un enlace serie que no crece nunca.** Por el
cableado viajan números, no voltajes. Un módulo nuevo, o pasar de 4 a 8
voces, suma **cero hilos**.

### El premio que no se buscaba: baja el suelo de afinación

El término dominante del presupuesto de masa existía porque el DAC y el VCO
referenciaban masas distintas: el CV de tono nacía en el cerebro y cruzaba el
bus para morir en el VCO. Con el DAC **en la misma placa** que los cuatro
osciladores, ese viaje desaparece — y con él, el término entero.

| Suelo del pitch | cents |
|---|---|
| DAC en el cerebro: masa del bus 1.21 + medida 0.50 | 1.71 |
| **DAC en la placa del VCO: plano local 0.08 + medida 0.50** | **0.58** |

Tres veces menos, y cambia quién manda: **el suelo pasa a ser la medida del
autoafinado, no la masa.** Los números — con la cota pesimista de layout y
sus aserciones — están en
[`hardware/03-vco/dac_local_budget.py`](../hardware/03-vco/dac_local_budget.py),
ejecutable.

Y lo que NO mejora, dicho claro: **el CV patcheado entre módulos sigue viendo
el bus.** Para el patch bay siguen mandando los 1.21 cents y todas las reglas
de `ground_budget.py`. El bus board no pierde ni una regla — ahora protege al
patch en vez de al pitch.

### La condición: la referencia

La VREF no puede venir por el bus — el error de masa se mudaría a ella
entero. Cada placa necesita su propia referencia de precisión, y ahí **el
grado importa**: el contrato exige ≤5 ppm/°C máximo (el techo de grado B del
AD5686R); a 20 ppm/°C máximo (grado A) son 3.4 cents de deriva, no cabe.

**Cómo se materializa queda a criterio de cada placa** — el principio es que
la VREF no cruce el bus, no que sea la interna de un DAC en concreto. El
módulo 3 (§10) lo resolvió con una **ADR4525BRZ** dedicada, compartida por
sus 3 DAC y sus 4 osciladores, con las referencias internas de los DAC
apagadas por firmware (registro `0111`): 2 ppm/°C máximo, mejor que el
propio techo del contrato. (Verificado en el datasheet de ADI; ojo también
con la variante -EP del AD5686R, 13 ppm/°C, que ya engañó una vez a
`tuning_budget.py`.)

Dos propiedades hacen la condición barata:

- **Una referencia sirve a las 4 voces** — el módulo 3 es una placa, no
  cuatro (§1) — así que su deriva es *común*: desplaza el teclado entero, no
  el acorde, y el autoafinado la reabsorbe en la siguiente pasada.
- **Su tolerancia estática (±2.5 mV) la absorbe `tuning.json`**, como
  cualquier error que no se mueve después de calibrar.

### Lo práctico

- **La lógica se alimenta local.** El conector SAM17 lleva ±12 V y masa, no
  5 V. Cada módulo con DAC se hace su lógica con un **regulador local desde
  +12 V**. Es carga de un solo riel — retorna entera por masa — pero son un
  par de mA, dentro de la holgura de `I_MASA_SAM17`.
- **El mismo enlace sirve a los digipots del ADSR** (AD5293, que es SPI): el
  enlace serie no es «para los DAC», es el sistema nervioso de todos los
  mandos de §7.
- **El direccionamiento** — cadena SPI contra chip-select decodificado — se
  decide al dibujar el módulo 3: issue #34, con los pros de cada uno ya
  escritos.

## 9. La alimentación aguanta, y con holgura

Estimación para 4 voces completas, por riel:

| Bloque | Consumo |
|---|---|
| Módulo 3 (VCO x4, SSI2130) | ~35 mA |
| 4× VCF + 4× VCA (LM13700) | ~21 mA |
| 4× ADSR | ~4 mA |
| Op-amps de todo el instrumento (~8 TL074) | ~45 mA |
| Módulo 2 (DAC + buffers) | ~11 mA |
| **Total** | **~116 mA** |

Contra los **650 mA/riel** del módulo 1 — con más holgura de la que se pensaba:
la fila del módulo 3 era una estimación de la tesis (4× CEM3340, 80 mA); medido
contra el diseño real ([`dac_local_budget.py`](../hardware/03-vco/dac_local_budget.py)),
el módulo entero — VCO, DAC, referencia y telemetría — pide ~35 mA. Sobra para
8 voces (~176 mA, doblando los bloques que escalan con voces) sin tocar la
fuente, contra los ~300 mA que daba la cuenta vieja. El respin de la fuente ya
dejó sitio para crecer aunque entonces todavía era un sinte mono.

**Lo que no cabe es la pantalla en el +5 V.** El táctil de 7" pide 450–550 mA y
el riel de +5 V está acotado a 300 mA por diseño (módulo 1 §16.12). Va alimentada
desde la fuente USB del propio Pi, que es lo que hace el diseño oficial de
Raspberry Pi de todas formas. Esa fuente sube de 2.5 A a **3 A**.

## 10. Lo que esto le exige a los módulos que faltan

El módulo 3 ya está dibujado; los otros tres (5, 6, 7) no, así que es el
momento de imponerles esto.

**Módulo 3 — VCO.** Pasa de 3 osciladores independientes a **4 canales
idénticos SSI2130** (Sound Semiconductor) con un solo juego de mandos — no el
CEM3340 de la tesis: el mezclador de 5 canales y el generador de seno viven
dentro del propio chip, y su compensación térmica en chip se lleva por delante
la R_TEMPCO. **Sin trimmers**: la escala de tono la fijan una única
**ADR4525BRZ** (referencia de toda la placa, compartida por el DAC y los
cuatro osciladores) y resistencias del 1 %, y el autoafinado absorbe el resto.
El bloque digital son **3× AD5686 en cadena soldada** (DCEN) — 12 canales, 9
en uso (pitch×4, PWM, mezcla×4) y 3 de reserva — con las tres referencias
internas de los DAC apagadas por firmware para dejar mandar a la ADR4525BRZ.
Necesita algo que la tesis no tiene: una **salida `TUNE_OUT` DIGITAL por
oscilador** — el `SQUARE OUT` de cada SSI2130 recortado a nivel lógico con un
74HC14, en la propia placa, no la señal analógica. Sin eso el autoafinado
exige patchear cables a mano y deja de ser automático, y meter audio por el
bus lo ensuciaría (§5). Lleva también la telemetría de serie de §8 (sensor de
temperatura + EEPROM de calibración). Es el primer módulo que cuelga del
enlace serie, y al dibujarlo se cerró el direccionamiento: híbrido
CS-por-módulo entre placas, cadena soldada dentro de cada una (issue #34).
**Ya está dibujado y verificado**: esquemático con ERC 0 errores/avisos, PCB
con DRC 0 infracciones, y salidas de fabricación listas para pedir a JLCPCB.
Spec: [`docs/superpowers/specs/2026-08-16-modulo-3-vco-design.md`](superpowers/specs/2026-08-16-modulo-3-vco-design.md).
Bring-up: [`hardware/03-vco/notes/bring-up.md`](../hardware/03-vco/notes/bring-up.md).
Números: [`dac_local_budget.py`](../hardware/03-vco/dac_local_budget.py).

**Módulo 5 — VCF.** Cuatro filtros idénticos, corte y resonancia comunes, **por
CV desde el DAC — que vive en esta placa (§8) —, no por potenciómetro** (§7).
Y ojo con la resonancia: en
topología MS-20 el pote está EN el audio, así que ahí va un VCA, no un digipot. El
apareamiento entre los cuatro importa: si no filtran igual, el acorde suena
desparejo. Hay que decidir si se ajusta canal a canal con trimmers.

**Módulo 6 — ADSR.** Cuatro envolventes, un juego de mandos, **cuatro gates
independientes**. Es el único módulo donde el DAC no basta: los tiempos son una
RC y hace falta **resistencia controlable** — OTA, JFET o digipot (§7), que si
es digipot cuelga del mismo enlace serie que los DAC (§8). Es el que más
cambia: en mono era un disparo, aquí son cuatro que corren a la vez y sin
relación entre sí.

**Módulo 7 — VCA.** Cuatro, con la envolvente de su voz y su velocity — cuyo
CV nace en el DAC de esta placa (§8).

**Módulo 4 — Mixer.** Se mueve al final de la cadena (§3) y pasa de sumar tres
osciladores a sumar cuatro voces ya filtradas.

## 11. Lo que NO está confirmado

1. **El jitter de 5 µs** del sellado de tiempos del Pi es de manual, no medido
   en la placa real. Todo el cálculo de autoafinado es proporcional a él. Si
   sale peor, un 74HC4040 dividiendo por 16 lo arregla.
2. **El consumo de 20 mA por CEM3340** era la estimación de la tesis para el
   VCO del módulo 1 — **obsoleta** desde que el módulo 3 pasó a SSI2130: su
   consumo real está medido, no estimado (~35 mA el módulo entero, no 20 mA
   por chip; spec del módulo 3 §9, `dac_local_budget.py`).
3. **El apareamiento entre los 4 filtros** no está estudiado. Es probablemente
   el problema más difícil de todo el instrumento polifónico, y no se resuelve
   con calibración digital como el tono: no hay nada que "escuche" el filtro.
4. **La asignación de voces con robo** tiene decisiones que se oyen (cuál robar,
   si hacer retrigger, legato) y todavía no están tomadas.
5. **El AD5686R encadenado** está en su tabla de comandos (bit 1000, *daisy-chain
   enable*) y sigue sin probarse con chips reales — ahora es **bloqueante**:
   el módulo 3 pone tres en cadena soldada, y sin ese passthrough no hay
   control de tono (spec del módulo 3 §11.7, Paso 3 del bring-up).
6. **Cuántos CV hacen falta en total** sigue abierto para los módulos 5, 6 y
   7, que no están dibujados. Para el módulo 3 ya se cerró: **12 canales** en
   3× AD5686 en cadena (9 en uso, 3 de reserva). La estimación de 15-20 CV
   del instrumento entero, repartidos por módulo (§8), sigue en pie para lo
   que falta.
7. **El zipper noise** de mover un parámetro con un DAC no está evaluado. A 16
   bits debería ser inaudible, pero en un barrido rápido de corte hay que
   comprobarlo y probablemente suavizar por software.
8. **Qué parámetro cae en cada uno de los tres casos** de §7 se decide módulo a
   módulo al dibujarlos, no antes.
9. **El direccionamiento del enlace serie** — **CERRADO** (issue #34, al
   dibujar el módulo 3): híbrido CS-por-módulo entre placas, con los chips de
   cada placa en cadena soldada (DCEN al arranque). Detalle en el
   [spec del módulo 3](superpowers/specs/2026-08-16-modulo-3-vco-design.md)
   §2.5 y §7.
10. **La apuesta trimless del módulo 3** — span de 7 octavas sin trimmers,
    con solo un 7.6 % de margen — depende de la dispersión chip a chip del
    convertidor exponencial del SSI2130, que ningún datasheet garantiza. Se
    cobra en el Paso 5 del bring-up (spec del módulo 3 §11.2); si una voz cae
    fuera, el bodge previsto es cambiar su `R_PITCH`, no un re-spin.
11. Nada de esto está medido. Son cálculos y datasheets.
