# Arquitectura polifónica del SAM17

> Este documento **sustituye** al diagrama monofónico de
> [`architecture.md`](architecture.md) como diseño vigente. Aquel queda como
> referencia de lo que hace la tesis, que es el punto de partida y no el
> destino.

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

Lo que hace:

- **Asignación de voces.** Decide qué nota va a qué voz, con robo de voz cuando
  llegan más notas que voces. Es una decisión de software y por eso vive aquí.
- **4 CV de tono**, 1 V/octava.
- **4 CV de velocity**, para que cada nota tenga su propio ataque.
- **4 gates** independientes.
- **Autoafinado** de los cuatro osciladores, midiendo las cuatro a la vez
  sobre pulsos lógicos que le llegan del módulo 3 (§5).
- **La interfaz**: pantalla táctil de 7", que es lo que hace usable la
  configuración de un poly.

## 3. Diagrama de bloques

```
        USB MIDI ──┐
        DIN MIDI ──┤
                   ▼
        ┌──────────────────────────────────┐
        │       MÓDULO 2 — EL CEREBRO      │
        │  Raspberry Pi + táctil 7"        │
        │  2x AD5686R (8 CV) encadenados   │
        │  asignación de voces + autoafinado│
        └─┬────┬────┬────┬─────────┬───────┘
   TONO 1-4│    │    │    │  GATE 1-4       │ escucha
          ▼    ▼    ▼    ▼         ▼         ▲
     ┌─────────────────────────────────┐     │
     │  MÓDULO 3 — VCO x4              │     │
     │  4x CEM3340 + 74HC14            │─────┘  4x pulso logico
     │  un juego de mandos             │        (TUNE_OUT digital)
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

El mixer se mueve **al final**. En el diseño monofónico sumaba los tres VCO
antes del filtro; aquí no puede, porque cada voz tiene que atravesar su propio
filtro y su propio VCA antes de mezclarse con las demás. **Sumar antes sería
parafónico, no polifónico** — y es exactamente la diferencia entre los dos.

## 4. Convenciones eléctricas

| Señal | Rango | Cantidad | Notas |
|-------|-------|----------|-------|
| `CV_PITCH_n` | **0 – 7 V** | 4 | 1 V/oct, 7 octavas (C1–C8). Cambia respecto a los 3–10 V de la tesis: ver issue #18 |
| `CV_VEL_n` | 0 – 7 V | 4 | Velocity por voz |
| `GATE_n` | 0 / 10 V | 4 | Activo alto |
| `TUNE_OUT_n` | **lógico 3.3 V** | 4 | **Nuevo**: onda del VCO ya recortada, para medir su frecuencia. Digital a propósito (§5) |
| `+12V` / `-12V` | ±12 V | — | 650 mA por riel |
| `+5V` | 5 V | — | Solo el DAC. **La pantalla NO cuelga de aquí** (§6) |
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
calibrar.

| | cents |
|---|---|
| Masa del bus board | **1.21** |
| Medida del autoafinado | 0.50 |
| **Suelo del instrumento** | **1.71** |

Y la deriva del VCO — que sin autoafinado no está acotada, porque el convertidor
exponencial arrastra −0.33 %/°C y su compensador hay que ajustarlo — **deja de
contar**.

O sea: el suelo del instrumento pasa a ser el bus board. Que es justo lo que se
arregló primero, antes de saber que iba a ser polifónico.

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

## 7. La alimentación aguanta, y con holgura

Estimación para 4 voces completas, por riel:

| Bloque | Consumo |
|---|---|
| 4× CEM3340 | 80 mA |
| 4× VCF + 4× VCA (LM13700) | ~21 mA |
| 4× ADSR | ~4 mA |
| Op-amps de todo el instrumento (~8 TL074) | ~45 mA |
| Módulo 2 (DAC + buffers) | ~11 mA |
| **Total** | **~160 mA** |

Contra los **650 mA/riel** del módulo 1. Sobra para 8 voces (~300 mA) sin tocar
la fuente. El respin de la fuente ya dejó sitio para crecer aunque entonces
todavía era un sinte mono.

**Lo que no cabe es la pantalla en el +5 V.** El táctil de 7" pide 450–550 mA y
el riel de +5 V está acotado a 300 mA por diseño (módulo 1 §16.12). Va alimentada
desde la fuente USB del propio Pi, que es lo que hace el diseño oficial de
Raspberry Pi de todas formas. Esa fuente sube de 2.5 A a **3 A**.

## 8. Lo que esto le exige a los módulos que faltan

Ninguno de los cuatro está dibujado, así que es el momento de imponerlo.

**Módulo 3 — VCO.** Pasa de 3 osciladores independientes a **4 canales
idénticos** con un solo juego de mandos. Y necesita algo que la tesis no tiene:
una **salida `TUNE_OUT` DIGITAL por oscilador** — la onda recortada a nivel
lógico con un 74HC14 en la propia placa, no la señal analógica. Sin eso el
autoafinado exige patchear cables a mano y deja de ser automático, y meter audio
por el bus lo ensuciaría (§5).

**Módulo 5 — VCF.** Cuatro filtros idénticos, corte y resonancia comunes. El
apareamiento entre los cuatro importa: si no filtran igual, el acorde suena
desparejo. Hay que decidir si se ajusta canal a canal con trimmers.

**Módulo 6 — ADSR.** Cuatro envolventes, un juego de mandos, **cuatro gates
independientes**. Es el que más cambia: en mono era un disparo, aquí son cuatro
que corren a la vez y sin relación entre sí.

**Módulo 7 — VCA.** Cuatro, con la envolvente de su voz y su velocity.

**Módulo 4 — Mixer.** Se mueve al final de la cadena (§3) y pasa de sumar tres
osciladores a sumar cuatro voces ya filtradas.

## 9. Lo que NO está confirmado

1. **El jitter de 5 µs** del sellado de tiempos del Pi es de manual, no medido
   en la placa real. Todo el cálculo de autoafinado es proporcional a él. Si
   sale peor, un 74HC4040 dividiendo por 16 lo arregla.
2. **El consumo de 20 mA por CEM3340** viene de la tesis (§8 del módulo 1 ya lo
   marcaba como zona gris). Con cuatro en vez de tres, un error ahí se
   multiplica.
3. **El apareamiento entre los 4 filtros** no está estudiado. Es probablemente
   el problema más difícil de todo el instrumento polifónico, y no se resuelve
   con calibración digital como el tono: no hay nada que "escuche" el filtro.
4. **La asignación de voces con robo** tiene decisiones que se oyen (cuál robar,
   si hacer retrigger, legato) y todavía no están tomadas.
5. **El AD5686R encadenado** está en su tabla de comandos (bit 1000, *daisy-chain
   enable*) pero no se ha probado con dos chips reales.
6. Nada de esto está medido. Son cálculos y datasheets.
