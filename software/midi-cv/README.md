# Firmware del módulo MIDI/CV

Implementación moderna en Python del firmware que se ejecuta en el
Raspberry Pi 3B+ del módulo MIDI/CV. Convierte mensajes MIDI USB en señales
**CV (1 V/oct)** y **GATE (10 V)** mediante un DAC AD5686R por SPI.

> Reemplaza al código original de la tesis (Capítulo III — *Diseño del
> Software*), conservando la misma arquitectura de modos pero con tipado
> estricto, separación de responsabilidades y código testeable fuera del
> Pi.

## Requisitos

- Python ≥ 3.10
- Raspberry Pi OS (Bullseye o más reciente) con SPI habilitado
  (`raspi-config → Interface Options → SPI → Enable`).
- Controlador MIDI USB clase compliant.
- Pantalla LCD 16×2 HD44780 cableada según [`docs/modules/02-midi-cv.md`](../../docs/modules/02-midi-cv.md).

## Instalación

En el Raspberry Pi:

```bash
cd software/midi-cv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[rpi]"
```

En tu máquina (sin hardware), para desarrollar y correr tests:

```bash
cd software/midi-cv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Ejecución

```bash
sam17-midicv                      # arranca el bucle principal con LCD + botones
sam17-midicv --mode standard
sam17-midicv --mode tune --vco VCO1
sam17-midicv --generate-tuning    # reescribe tuning.json con la curva 1 V/oct
sam17-midicv --dry-run            # cablea todo con stubs y sale (smoke test)
```

`--dry-run` no toca GPIO, SPI ni MIDI, así que corre en cualquier máquina.

En arranque automático del Pi: añade un servicio `systemd` (ver
`scripts/sam17-midicv.service`).

## Arquitectura

```
sam17/
├── __init__.py
├── __main__.py         Entry-point CLI
├── app.py              Bucle principal, menú y cambio de modo
├── settings.py         Configuración global (pines, SPI, rangos, paths)
├── calibration.py      Curva 1 V/oct y persistencia de la afinación
├── data/
│   ├── notes.json      Mapa MIDI note → nombre (C1, C#1, …)
│   └── tuning.json     Calibración por VCO (curva de diseño + correcciones)
├── hardware/
│   ├── __init__.py
│   ├── dac.py          Driver del AD5686R (envío de tramas SPI 24-bit)
│   ├── gpio.py         Wrappers de GPIO (con stubs para tests)
│   ├── lcd.py          Driver del LCD 16x2
│   └── buttons.py      Polling/interrupciones de los 4 botones
├── midi/
│   ├── __init__.py
│   ├── controller.py   Detección/apertura del controlador MIDI USB
│   └── usb_detector.py Watcher de eventos hot-plug del puerto USB
├── modes/
│   ├── __init__.py
│   ├── base.py         Interfaz `Mode` común
│   ├── standard.py     Conversión MIDI→CV monofónica con pitch-bend
│   ├── tune.py         Modo de afinación interactiva
│   ├── glide.py        (pendiente)
│   ├── arp.py          (pendiente)
│   └── step_sequencer.py (pendiente)
└── ui/
    ├── __init__.py
    └── menu.py         Menú navegable por LCD/botones
```

## Tests

Los tests usan `pytest` y stubs de `RPi.GPIO` y `spidev` que se inyectan
desde `tests/conftest.py`, de modo que se ejecutan en cualquier máquina
sin hardware.

```bash
pytest
pytest --cov=sam17
```

## Diferencias respecto al código de la tesis

| Aspecto | Tesis (2020) | Este firmware |
|---------|--------------|---------------|
| Estructura | Scripts sueltos, `settings.py` lleno de globales | Paquete con módulos por responsabilidad |
| Persistencia | `pickle` (`notes.pickle`, `afinacion.pickle`) | JSON (`notes.json`, `tuning.json`) |
| `__init__` / `__call__` | Tipos con guion bajo simple (bug) | `__dunder__` correcto |
| LCD | `Adafruit_CharLCD` (deprecado) | `RPLCD` con interfaz abstracta |
| Tests | Ninguno | `pytest` con stubs de GPIO/SPI |
| Modos de ejecución | 2 implementados, 3 declarados | Mismos 2 + 3 rechazados con aviso en el LCD |
| Estado | Globales en `settings.init()` | Explícito en `App` |
| Afinación | `afinacion.pickle` hecho a mano, perdido | Curva 1 V/oct generable + corrección persistida |

## Afinación

`tuning.json` arranca con la **curva de diseño**: 460 cuentas de DAC por semitono
(la constante `note_res` de la tesis), o sea 1 V/octava exacto. El hardware real
se desvía —la tesis midió +0.45 % en el VCO1, −3.32 % en el VCO2 y −18.62 % en el
VCO3— y esa desviación se corrige nota por nota con `--mode tune`, contra un
afinador externo, usando UP/DOWN para ajustar y ENTER para guardar.

El paso de ajuste (`NUDGE_COUNTS`, ~1 cent) está en `modes/tune.py`; súbelo si
afinar a oído resulta lento.

## Próximos pasos

- Implementar **glide / arp / step sequencer**: la tesis los declara en
  `settings.modos` pero nunca los escribió (ver [`docs/thesis-software.md`](../../docs/thesis-software.md)).
- Ver `docs/modules/02-midi-cv.md`, sección *Mejoras propuestas*.
