# Hardware — Módulo 2: MIDI/CV

> Documentación funcional: [`docs/modules/02-midi-cv.md`](../../docs/modules/02-midi-cv.md).
> Firmware: [`software/midi-cv/`](../../software/midi-cv).

## Resumen

El único módulo digital del sintetizador. Combina un Raspberry Pi 3B+ con un
DAC AD5686R (16-bit, cuádruple) para generar 3 salidas CV (1 V/oct) y 1
GATE digital (10 V) a partir de mensajes MIDI USB.

## Componentes principales

| Función | Componente |
|---------|------------|
| Procesamiento + USB MIDI | Raspberry Pi 3B+ |
| Conversión D/A (4 canales 16-bit) | AD5686R |
| Buffer/escalado CV | TL074 (op-amp) |
| Pantalla menú | LCD 16×2 (HD44850 / HD44780 compat.) |
| Navegación | 4 pulsadores táctiles |

## Pinout (ver `docs/modules/02-midi-cv.md`)

GPIO BCM: UP=4, DOWN=17, BACK=16, ENTER=26, GATE=27, DAC RESET=6.
LCD: RS=25, EN=24, D4=23, D5=18, D6=15, D7=14.
SPI: bus 0, device 1, mode `0b01`, max 50 MHz.

## Estructura del directorio

```
02-midi-cv/
├── README.md
├── bom.csv
├── kicad/      (pendiente — esquema de la placa de DAC y buffers)
├── schematics/ (pendiente)
├── pcb/        (pendiente)
└── notes/      (pendiente — diseño térmico, calibración)
```

## Estado

- [ ] Esquemático en KiCad
- [ ] PCB ruteada
- [ ] Calibración fina de las salidas CV (1 V/oct)
- [ ] Validación SPI con osciloscopio
- [ ] Diseño térmico del Raspberry Pi (ventilación + disipadores)
