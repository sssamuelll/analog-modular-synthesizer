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
- **Autoafinado** de los cuatro osciladores (§5).
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
     │  4x CEM3340, un juego de mandos │─────┘  (mux 74HC4051)
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
| `TUNE_OUT_n` | audio | 4 | **Nuevo**: salida dedicada de cada VCO hacia el multiplexor de escucha |
| `+12V` / `-12V` | ±12 V | — | 650 mA por riel |
| `+5V` | 5 V | — | Solo el DAC. **La pantalla NO cuelga de aquí** (§6) |
| `GNDA` / `GNDD` | — | — | Masas partidas, se unen solo en la estrella del módulo 1 |

## 5. Autoafinado

Con una sola voz, un oscilador desafinado suena raro. **Con cuatro, suena mal de
una forma que no se puede ignorar**: los batidos entre voces delatan errores que
en monofónico ni notas. Por eso en un poly analógico el autoafinado no es un
lujo, es infraestructura.

### Cómo escucha

Un **multiplexor analógico 74HC4051** en el módulo 2 recibe las 4 salidas
`TUNE_OUT` y selecciona cuál se mide. La señal seleccionada pasa por un
atenuador, acoplo AC y un disparador Schmitt a 3.3 V, y de ahí a un GPIO.

Coste en pines: **3 de dirección + 1 de habilitación + 1 de medida = 5 GPIO**,
para 8 osciladores. **No crece con las voces**, que es la razón de usar mux en
vez de una entrada por VCO.

### Cómo mide

**Conteo recíproco**: se cronometra cuánto tardan N periodos y se saca `f = N/T`.
Es lo contrario de contar ciclos por segundo, y es mucho mejor en las notas
graves — que es donde el otro método se queda corto.

Los números están en
[`hardware/02-midi-cv/autotune_budget.py`](../hardware/02-midi-cv/autotune_budget.py),
que es ejecutable:

| | |
|---|---|
| Barrido completo 84 notas × 4 voces | **~14 s** |
| Precisión de la medida | **0.5 cents** peor caso |
| Carga para el Pi | 72 flancos por medida, sin divisor por hardware |

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

## 6. La alimentación aguanta, y con holgura

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

## 7. Lo que esto le exige a los módulos que faltan

Ninguno de los cuatro está dibujado, así que es el momento de imponerlo.

**Módulo 3 — VCO.** Pasa de 3 osciladores independientes a **4 canales
idénticos** con un solo juego de mandos. Y necesita algo que la tesis no tiene:
una **salida `TUNE_OUT` dedicada por oscilador** hacia el módulo 2, además de la
que va al filtro. Sin eso el autoafinado exige patchear cables a mano y deja de
ser automático.

**Módulo 5 — VCF.** Cuatro filtros idénticos, corte y resonancia comunes. El
apareamiento entre los cuatro importa: si no filtran igual, el acorde suena
desparejo. Hay que decidir si se ajusta canal a canal con trimmers.

**Módulo 6 — ADSR.** Cuatro envolventes, un juego de mandos, **cuatro gates
independientes**. Es el que más cambia: en mono era un disparo, aquí son cuatro
que corren a la vez y sin relación entre sí.

**Módulo 7 — VCA.** Cuatro, con la envolvente de su voz y su velocity.

**Módulo 4 — Mixer.** Se mueve al final de la cadena (§3) y pasa de sumar tres
osciladores a sumar cuatro voces ya filtradas.

## 8. Lo que NO está confirmado

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
