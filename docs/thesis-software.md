# Recuperación del software desde la tesis

Este documento registra **qué contiene realmente** el PDF (`docs/thesis.pdf`) sobre
el firmware del módulo MIDI/CV, qué se pudo recuperar literalmente y qué hubo que
reconstruir. Sirve para que nadie vuelva a abrir las 154 páginas buscando el código.

## Dónde está el software en el PDF

| Páginas PDF | Páginas impresas | Contenido |
|-------------|------------------|-----------|
| 50 | 36 | *Diseño del Software* — librerías usadas |
| 51–69 | 37–55 | *Código del Programa* — los siete módulos |
| 132–134 | 118–120 | Tabla 11 — medición de CV de entrada por nota en los VCOs |

El capítulo de código es **texto seleccionable**, no capturas de pantalla: no hay
imágenes en las páginas 50–69. No existe anexo de código fuente — los anexos son
hojas de datos de componentes (Anexo A) y el resumen curricular (Anexo B).

## Qué trae y qué falta

Los siete módulos del original y su estado en el PDF:

| Módulo original | Estado en el PDF | Dónde vive hoy |
|-----------------|------------------|----------------|
| `midicontroller.py` | Completo salvo el cuerpo de `getmidicontroller()`, cortado con `…` | `sam17/midi/controller.py` |
| `usbdetect.py` | Cortado en `if device.action == 'add'…` | `sam17/midi/usb_detector.py` |
| `pitodac.py` | Completo | `sam17/hardware/dac.py` |
| `display.py` | Completo | `sam17/hardware/lcd.py` |
| `settings.py` | Completo (todas las globales, pines, direcciones del DAC) | `sam17/settings.py` |
| `bottons.py` | Sólo el `GPIO.setup` y los `add_event_detect`; los callbacks nunca se muestran | `sam17/hardware/buttons.py` |
| Modo estándar | El bloque `if` del bucle, completo | `sam17/modes/standard.py` |
| Modo de afinación | El bloque `if` del bucle, completo | `sam17/modes/tune.py` |

**Nunca aparecen en el PDF**, ni completos ni truncados:

- El `while True` que envuelve los dos modos, ni el arranque del programa.
- Los callbacks de los botones (`entro`, `atras`, `arriba`, `abajo`).
- La lógica del menú del LCD, aunque las listas de opciones sí están
  (`menup_list`, `menuc_list`, `menuh_list`, `helptune_list`).
- Los tres pickles: `notes.pickle`, `afinacion.pickle`, `helper.pickle`.
- Los modos **glide**, **arp** y **step sequencer**: sólo existen como cadenas
  dentro de `settings.modos`. Nunca se implementaron.

## Reconstruido

- **`sam17/app.py`** — el bucle principal y el despacho por modo. Misma semántica
  que la tesis (`receive(block=False)` no bloqueante, prioridad de última nota,
  GATE alto mientras haya nota), con el estado explícito en vez de globales.
- **`sam17/calibration.py`** — la curva 1 V/octava. `afinacion.pickle` se perdió,
  pero el PDF conserva la constante que lo generaba: `note_res = 460` cuentas de
  DAC por semitono, es decir 5520 cuentas por voltio. La curva de diseño es
  `valor(nota) = 18437 + (nota − 36) × 460`, donde 18437 cuentas ≈ 3.34 V, el CV
  medido para la nota más grave del VCO1 (Tabla 11).
- **`sam17/modes/tune.py`** — el ajuste con UP/DOWN y el guardado con ENTER, que
  la tesis describe en prosa pero no muestra en código. Los textos de la guía sí
  son literales del original (`HELP_STEPS`).
- **`docs/reference/vco-cv-measurements.csv`** — la Tabla 11 extraída a CSV.

## Errores del original que no se replicaron

- `def _init_` y `def _call_` con un solo guion bajo: nunca fueron `__init__` ni
  `__call__`, así que el decorador `@Midicontroller` no funcionaba como se describe.
- `GPIO.setup(settings.gate, GPIO.LOW)` para mover el GATE: `setup` configura el
  pin, no escribe en él. Debía ser `GPIO.output`.
- La pila de ocho booleanos (`first`, `second`, … `eight`) para llevar las notas
  pisadas: aquí es una lista con prioridad de última nota.
- `spi.max_speed_hz = 50_000_000`: el AD5686R admite 50 MHz, pero el bus SPI del
  Raspberry Pi no llega; el kernel lo recorta al divisor más cercano. Se dejó el
  valor del original porque es inofensivo.

## Sobre la Tabla 11

73 notas (MIDI 36–108) con el CV medido en la entrada de cada VCO.

- La tesis numera las notas una octava por debajo de la convención científica:
  su `C1` es MIDI 36, que es `C2` con C4 = do central. El CSV trae ambas columnas.
- Hay una errata en los ids 52 y 53, etiquetados `C#5` y `C5` cuando por posición
  corresponden a `D#5` y `E5` (columna `note_thesis`); la columna `midi_note` es
  la buena.
- El VCO3 sólo llega hasta el id 61 (MIDI 96): la tesis lo reporta como una
  limitación real del canal, "no llega sino a 5 octavas".
- Pendientes medidas: VCO1 +0.45 %, VCO2 −3.32 %, VCO3 −18.62 % respecto de
  1 V/octava. Esa desviación es exactamente lo que corrige el modo de afinación.
